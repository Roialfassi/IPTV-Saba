/**
 * Client-side download manager using Service Workers for offline support
 */

interface DownloadItem {
    id: string;
    url: string;
    title: string;
    progress: number;
    status: 'downloading' | 'completed' | 'failed';
}

class DownloadManager {
    private downloads: Map<string, DownloadItem> = new Map();
    private db: IDBDatabase | null = null;

    async init() {
        // Initialize IndexedDB for storing downloaded content
        return new Promise<void>((resolve, reject) => {
            const request = indexedDB.open('IPTVDownloads', 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = (event.target as IDBOpenDBRequest).result;

                if (!db.objectStoreNames.contains('downloads')) {
                    const store = db.createObjectStore('downloads', { keyPath: 'id' });
                    store.createIndex('status', 'status', { unique: false });
                }

                if (!db.objectStoreNames.contains('files')) {
                    db.createObjectStore('files', { keyPath: 'id' });
                }
            };
        });
    }

    async downloadContent(
        id: string,
        url: string,
        title: string,
        onProgress?: (progress: number) => void
    ): Promise<void> {
        const downloadItem: DownloadItem = {
            id,
            url,
            title,
            progress: 0,
            status: 'downloading',
        };

        this.downloads.set(id, downloadItem);

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Download failed');

            const contentLength = parseInt(
                response.headers.get('content-length') || '0'
            );
            const reader = response.body?.getReader();
            if (!reader) throw new Error('No reader available');

            const chunks: Uint8Array[] = [];
            let receivedLength = 0;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                chunks.push(value);
                receivedLength += value.length;

                const progress = (receivedLength / contentLength) * 100;
                downloadItem.progress = progress;
                onProgress?.(progress);
            }

            // Combine chunks
            const blob = new Blob(chunks);

            // Store in IndexedDB
            await this.saveToIndexedDB(id, {
                id,
                title,
                url,
                blob,
                downloadedAt: new Date().toISOString(),
            });

            downloadItem.status = 'completed';
            downloadItem.progress = 100;
        } catch (error) {
            console.error('Download failed:', error);
            downloadItem.status = 'failed';
            throw error;
        }
    }

    private async saveToIndexedDB(id: string, data: any): Promise<void> {
        if (!this.db) throw new Error('Database not initialized');

        return new Promise((resolve, reject) => {
            const transaction = this.db!.transaction(['files'], 'readwrite');
            const store = transaction.objectStore('files');
            const request = store.put(data);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async getDownloadedContent(id: string): Promise<Blob | null> {
        if (!this.db) throw new Error('Database not initialized');

        return new Promise((resolve, reject) => {
            const transaction = this.db!.transaction(['files'], 'readonly');
            const store = transaction.objectStore('files');
            const request = store.get(id);

            request.onsuccess = () => {
                const result = request.result;
                resolve(result ? result.blob : null);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getAllDownloads(): Promise<any[]> {
        if (!this.db) throw new Error('Database not initialized');

        return new Promise((resolve, reject) => {
            const transaction = this.db!.transaction(['files'], 'readonly');
            const store = transaction.objectStore('files');
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async deleteDownload(id: string): Promise<void> {
        if (!this.db) throw new Error('Database not initialized');

        return new Promise((resolve, reject) => {
            const transaction = this.db!.transaction(['files'], 'readwrite');
            const store = transaction.objectStore('files');
            const request = store.delete(id);

            request.onsuccess = () => {
                this.downloads.delete(id);
                resolve();
            };
            request.onerror = () => reject(request.error);
        });
    }

    getDownloadProgress(id: string): number {
        return this.downloads.get(id)?.progress || 0;
    }

    getDownloadStatus(id: string): string | null {
        return this.downloads.get(id)?.status || null;
    }
}

export const downloadManager = new DownloadManager();

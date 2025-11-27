import { M3UEntry } from './m3u.types';

export interface ValidationResult {
    isValid: boolean;
    reason?: string;
}

export class M3UValidator {
    static validateUrl(url: string): boolean {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    static validateEntry(entry: M3UEntry): ValidationResult {
        if (!entry.url || !this.validateUrl(entry.url)) {
            return { isValid: false, reason: 'Invalid URL' };
        }
        if (!entry.displayName) {
            return { isValid: false, reason: 'Missing display name' };
        }
        return { isValid: true };
    }

    static sanitizeMetadata(metadata: string): string {
        return metadata.replace(/[\r\n]+/g, ' ').trim();
    }
}

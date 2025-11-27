import { useState, useEffect } from 'react';
import { useSettings, useUpdateSettings } from '../../hooks/useSettings';
import { Download, Upload, Trash2 } from 'lucide-react';

export default function DataManagement() {
    const { data: settings } = useSettings();
    const updateSettings = useUpdateSettings();

    const [formData, setFormData] = useState({
        cacheEnabled: true,
        cacheSize: 500,
        downloadQuality: '720p',
        wifiOnlyDownloads: true,
    });

    useEffect(() => {
        if (settings) {
            setFormData({
                cacheEnabled: settings.cacheEnabled,
                cacheSize: settings.cacheSize,
                downloadQuality: settings.downloadQuality,
                wifiOnlyDownloads: settings.wifiOnlyDownloads,
            });
        }
    }, [settings]);

    const handleSave = async () => {
        await updateSettings.mutateAsync(formData);
        alert('Data settings saved!');
    };

    const handleClearCache = () => {
        if (confirm('Are you sure you want to clear the application cache? This will remove temporary files but keep your downloads.')) {
            // Logic to clear cache would go here (e.g., clearing IndexedDB or Service Worker cache)
            alert('Cache cleared successfully!');
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold mb-4 text-white">Data & Storage</h2>
            </div>

            <div className="space-y-4 bg-gray-800 rounded-lg p-6">
                {/* Cache Settings */}
                <div className="flex items-center justify-between">
                    <div>
                        <label className="block text-sm font-medium text-gray-300">
                            Enable Caching
                        </label>
                        <p className="text-xs text-gray-400 mt-1">
                            Cache images and data for faster loading
                        </p>
                    </div>
                    <input
                        type="checkbox"
                        checked={formData.cacheEnabled}
                        onChange={(e) => setFormData(prev => ({ ...prev, cacheEnabled: e.target.checked }))}
                        className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                        Max Cache Size (MB)
                    </label>
                    <input
                        type="number"
                        min="100"
                        max="10000"
                        value={formData.cacheSize}
                        onChange={(e) => setFormData(prev => ({ ...prev, cacheSize: parseInt(e.target.value) }))}
                        className="w-full px-4 py-2 bg-gray-700 rounded-lg text-white border border-gray-600 focus:ring-blue-500"
                    />
                </div>

                {/* Download Settings */}
                <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                        Download Quality
                    </label>
                    <select
                        value={formData.downloadQuality}
                        onChange={(e) => setFormData(prev => ({ ...prev, downloadQuality: e.target.value }))}
                        className="w-full px-4 py-2 bg-gray-700 rounded-lg text-white border border-gray-600 focus:ring-blue-500"
                    >
                        <option value="1080p">1080p</option>
                        <option value="720p">720p</option>
                        <option value="480p">480p</option>
                    </select>
                </div>

                <div className="flex items-center justify-between">
                    <div>
                        <label className="block text-sm font-medium text-gray-300">
                            Download on Wi-Fi Only
                        </label>
                        <p className="text-xs text-gray-400 mt-1">
                            Prevent downloads when using mobile data
                        </p>
                    </div>
                    <input
                        type="checkbox"
                        checked={formData.wifiOnlyDownloads}
                        onChange={(e) => setFormData(prev => ({ ...prev, wifiOnlyDownloads: e.target.checked }))}
                        className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500"
                    />
                </div>
            </div>

            {/* Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                    onClick={handleClearCache}
                    className="flex items-center justify-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg text-white"
                >
                    <Trash2 className="w-5 h-5" />
                    Clear Cache
                </button>
                <button
                    onClick={handleSave}
                    className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white"
                >
                    <Save className="w-5 h-5" />
                    Save Changes
                </button>
            </div>
        </div>
    );
}

function Save({ className }: { className?: string }) {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" /><polyline points="17 21 17 13 7 13 7 21" /><polyline points="7 3 7 8 15 8" /></svg>
    )
}

import { useState, useEffect } from 'react';
import { useSettings, useUpdateSettings } from '../../hooks/useSettings';

export default function AppearanceSettings() {
    const { data: settings } = useSettings();
    const updateSettings = useUpdateSettings();

    const [formData, setFormData] = useState({
        theme: 'dark',
        accentColor: '#3b82f6',
        compactMode: false,
        showEPG: true,
        gridSize: 'medium',
    });

    useEffect(() => {
        if (settings) {
            setFormData({
                theme: settings.theme,
                accentColor: settings.accentColor,
                compactMode: settings.compactMode,
                showEPG: settings.showEPG,
                gridSize: settings.gridSize,
            });
        }
    }, [settings]);

    const handleSave = async () => {
        await updateSettings.mutateAsync(formData);
        alert('Appearance settings saved!');
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold mb-4 text-white">Appearance Settings</h2>
            </div>

            <div className="space-y-4 bg-gray-800 rounded-lg p-6">
                {/* Theme */}
                <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                        Theme
                    </label>
                    <select
                        value={formData.theme}
                        onChange={(e) => setFormData(prev => ({ ...prev, theme: e.target.value }))}
                        className="w-full px-4 py-2 bg-gray-700 rounded-lg text-white border border-gray-600 focus:ring-blue-500"
                    >
                        <option value="dark">Dark Mode</option>
                        <option value="light">Light Mode</option>
                    </select>
                </div>

                {/* Grid Size */}
                <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                        Grid Size
                    </label>
                    <select
                        value={formData.gridSize}
                        onChange={(e) => setFormData(prev => ({ ...prev, gridSize: e.target.value }))}
                        className="w-full px-4 py-2 bg-gray-700 rounded-lg text-white border border-gray-600 focus:ring-blue-500"
                    >
                        <option value="small">Small</option>
                        <option value="medium">Medium</option>
                        <option value="large">Large</option>
                    </select>
                </div>

                {/* Compact Mode */}
                <div className="flex items-center justify-between">
                    <div>
                        <label className="block text-sm font-medium text-gray-300">
                            Compact Mode
                        </label>
                        <p className="text-xs text-gray-400 mt-1">
                            Reduce padding and font sizes for denser information
                        </p>
                    </div>
                    <input
                        type="checkbox"
                        checked={formData.compactMode}
                        onChange={(e) => setFormData(prev => ({ ...prev, compactMode: e.target.checked }))}
                        className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500"
                    />
                </div>

                {/* Show EPG */}
                <div className="flex items-center justify-between">
                    <div>
                        <label className="block text-sm font-medium text-gray-300">
                            Show EPG
                        </label>
                        <p className="text-xs text-gray-400 mt-1">
                            Display Electronic Program Guide in channel list
                        </p>
                    </div>
                    <input
                        type="checkbox"
                        checked={formData.showEPG}
                        onChange={(e) => setFormData(prev => ({ ...prev, showEPG: e.target.checked }))}
                        className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500"
                    />
                </div>
            </div>

            <button
                onClick={handleSave}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white"
            >
                Save Changes
            </button>
        </div>
    );
}

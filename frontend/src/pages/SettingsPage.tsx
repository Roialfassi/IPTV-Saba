import { useState } from 'react';
import { Settings, Play, Palette, Database, Bell } from 'lucide-react';
import GeneralSettings from '../components/settings/GeneralSettings';
import PlaybackSettings from '../components/settings/PlaybackSettings';
import AppearanceSettings from '../components/settings/AppearanceSettings';
import DataManagement from '../components/settings/DataManagement';

type SettingsTab = 'general' | 'playback' | 'appearance' | 'data';

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<SettingsTab>('general');

    const tabs = [
        { id: 'general', label: 'General', icon: Settings },
        { id: 'playback', label: 'Playback', icon: Play },
        { id: 'appearance', label: 'Appearance', icon: Palette },
        { id: 'data', label: 'Data & Storage', icon: Database },
    ];

    const renderContent = () => {
        switch (activeTab) {
            case 'general':
                return <GeneralSettings />;
            case 'playback':
                return <PlaybackSettings />;
            case 'appearance':
                return <AppearanceSettings />;
            case 'data':
                return <DataManagement />;
            default:
                return null;
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-white">Settings</h1>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Sidebar */}
                <div className="lg:col-span-1">
                    <div className="bg-gray-800 rounded-lg p-2 space-y-1">
                        {tabs.map((tab) => {
                            const Icon = tab.icon;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as SettingsTab)}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === tab.id
                                            ? 'bg-blue-600 text-white'
                                            : 'text-gray-300 hover:bg-gray-700'
                                        }`}
                                >
                                    <Icon className="w-5 h-5" />
                                    <span className="font-medium">{tab.label}</span>
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Content */}
                <div className="lg:col-span-3">
                    {renderContent()}
                </div>
            </div>
        </div>
    );
}

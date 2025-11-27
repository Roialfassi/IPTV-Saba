import { NavLink } from 'react-router-dom';
import { Home, Tv, Film, Clapperboard, Users, Settings } from 'lucide-react';
import clsx from 'clsx';

export default function Sidebar() {
    const navItems = [
        { name: 'Home', path: '/', icon: Home },
        { name: 'Live TV', path: '/channels', icon: Tv },
        { name: 'Movies', path: '/movies', icon: Film },
        { name: 'Series', path: '/series', icon: Clapperboard },
        { name: 'Profiles', path: '/profiles', icon: Users },
    ];

    return (
        <aside className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col">
            <div className="p-6">
                <h1 className="text-2xl font-bold text-blue-500">IPTV App</h1>
            </div>

            <nav className="flex-1 px-4 space-y-2">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            clsx(
                                'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                                isActive
                                    ? 'bg-blue-600 text-white'
                                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                            )
                        }
                    >
                        <item.icon size={20} />
                        <span className="font-medium">{item.name}</span>
                    </NavLink>
                ))}
            </nav>

            <div className="p-4 border-t border-gray-800">
                <button className="flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white w-full">
                    <Settings size={20} />
                    <span>Settings</span>
                </button>
            </div>
        </aside>
    );
}

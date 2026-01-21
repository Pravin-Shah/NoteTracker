import { useTags } from '../../hooks/useNotes';
import { useAuth } from '../../context/AuthContext';
import { LogOut } from 'lucide-react';

interface SidebarProps {
    selectedFolder: string;
    selectedTag: string | null;
    onFolderChange: (folder: string) => void;
    onTagClick: (tag: string) => void;
    onNewNote: () => void;
    isCollapsed: boolean;
    onToggleCollapse: () => void;
}

export default function Sidebar({
    selectedFolder,
    selectedTag,
    onFolderChange,
    onTagClick,
    onNewNote,
    isCollapsed,
    onToggleCollapse,
}: SidebarProps) {
    const { data: tags = [] } = useTags();
    const { user, logout } = useAuth();

    const folders = [
        { id: 'all', label: 'All Notes', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
        { id: 'favorites', label: 'Favorites', icon: 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z' },
        { id: 'trash', label: 'Trash', icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16' },
    ];

    const specialForms = [
        { id: 'daily-tracker', label: 'Daily Tracker', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
        { id: 'health-log', label: 'Health Log', icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z' },
    ];

    return (
        <div
            className={`${isCollapsed ? 'w-16' : 'w-60'} bg-[#1a1a1a] flex flex-col border-r border-gray-800 transition-all duration-300`}
            style={{ paddingLeft: '0.5rem', paddingRight: '0.5rem' }}
        >
            {/* Header with Toggle */}
            <div className="px-2 pt-4 pb-2 flex items-center justify-between">
                {!isCollapsed && <h1 className="text-lg font-semibold text-white">Notes</h1>}
                <button
                    onClick={onToggleCollapse}
                    className="p-1.5 hover:bg-[#333] rounded transition-colors text-gray-400 hover:text-white"
                    title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        {isCollapsed ? (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                        ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                        )}
                    </svg>
                </button>
            </div>

            {/* New Note Button */}
            <div className="px-2" style={{ paddingTop: '0.5rem', paddingBottom: '0.5rem' }}>
                <button
                    onClick={onNewNote}
                    className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'justify-center gap-2'} bg-[#2a2a2a] hover:bg-[#333] text-gray-200 py-2 px-3 rounded-md text-sm transition-colors border border-gray-700`}
                    title="New Note"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    {!isCollapsed && 'New Note'}
                </button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto px-1">
                {/* Folders */}
                <div className="flex flex-col mb-5" style={{ gap: '0.25rem' }}>
                    {folders.map((folder) => (
                        <button
                            key={folder.id}
                            onClick={() => onFolderChange(folder.id)}
                            className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-2.5'} text-left px-2.5 py-1.5 rounded-md text-[13px] transition-colors ${selectedFolder === folder.id && !selectedTag
                                ? 'bg-[#2a2a2a] text-white'
                                : 'text-gray-400 hover:bg-[#252525] hover:text-gray-200'
                                }`}
                            title={folder.label}
                        >
                            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={folder.icon} />
                            </svg>
                            {!isCollapsed && folder.label}
                        </button>
                    ))}
                </div>

                {/* Special Forms - Hidden when collapsed */}
                {!isCollapsed && (
                    <div className="mb-5" style={{ paddingTop: '0.5rem', paddingBottom: '0.5rem' }}>
                        <h3 className="text-[11px] font-medium text-gray-500 uppercase tracking-wider px-2.5" style={{ marginBottom: '0.75rem' }}>
                            Special Form
                        </h3>
                        <div className="flex flex-col" style={{ gap: '0.25rem' }}>
                            {specialForms.map((form) => (
                                <button
                                    key={form.id}
                                    onClick={() => onFolderChange(form.id)}
                                    className={`w-full flex items-center gap-2.5 text-left px-2.5 py-1.5 rounded-md text-[13px] transition-colors ${selectedFolder === form.id
                                        ? 'bg-[#2a2a2a] text-white'
                                        : 'text-gray-400 hover:bg-[#252525] hover:text-gray-200'
                                        }`}
                                >
                                    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={form.icon} />
                                    </svg>
                                    {form.label}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Tags Cloud - Hidden when collapsed */}
                {!isCollapsed && (
                    <div className="pb-4" style={{ paddingTop: '0.5rem', paddingBottom: '1rem' }}>
                        <h3 className="text-[11px] font-medium text-gray-500 uppercase tracking-wider px-2.5" style={{ marginBottom: '0.75rem' }}>
                            Tags Cloud
                        </h3>
                        <div className="flex flex-wrap gap-1.5 px-1">
                            {tags.map((tag) => (
                                <button
                                    key={tag}
                                    onClick={() => onTagClick(tag)}
                                    className={`text-[11px] px-2 py-0.5 rounded transition-colors ${selectedTag === tag
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-[#2a2a2a] text-gray-400 hover:bg-[#333] hover:text-gray-200'
                                        }`}
                                >
                                    #{tag}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* User Profile & Logout */}
            <div className="mt-auto px-2 py-4 border-t border-gray-800" style={{ paddingBottom: '1rem' }}>
                <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3 px-1'}`} style={{ marginBottom: '0.75rem' }}>
                    <img
                        src={user?.picture || `https://ui-avatars.com/api/?name=${user?.name || 'User'}&background=2563eb&color=fff`}
                        alt="Profile"
                        className="w-8 h-8 rounded-full border border-gray-700"
                    />
                    {!isCollapsed && (
                        <div className="flex-1 min-w-0">
                            <p className="text-[13px] font-medium text-white truncate">{user?.name}</p>
                            <p className="text-[11px] text-gray-500 truncate">{user?.email}</p>
                        </div>
                    )}
                </div>
                <button
                    onClick={logout}
                    className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-2 px-2'} py-2 text-gray-400 hover:text-white hover:bg-[#2a2a2a] rounded-md transition-colors text-[13px]`}
                    title="Logout"
                >
                    <LogOut className="w-4 h-4" />
                    {!isCollapsed && <span>Logout</span>}
                </button>
            </div>
        </div>
    );
}

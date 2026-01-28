import { useState } from 'react';
import Sidebar from './Sidebar';
import NotesFeed from './NotesFeed';
import NoteEditor from './NoteEditor';
import DailyTracker from '../habits/DailyTracker';

export default function NotesLayout() {
    const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [selectedFolder, setSelectedFolder] = useState<string>('all');
    const [selectedTag, setSelectedTag] = useState<string | null>(null);
    const [initialTags, setInitialTags] = useState<string[]>([]);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

    const handleNoteSelect = (noteId: number) => {
        setSelectedNoteId(noteId);
        setIsEditing(false);
        setInitialTags([]);
    };

    const handleNewNote = () => {
        setSelectedNoteId(null);
        setIsEditing(true);
        setInitialTags([]);
    };

    const handleNewNoteWithTags = (tags: string[]) => {
        setSelectedNoteId(null);
        setIsEditing(true);
        setInitialTags(tags);
    };

    const handleNoteCreated = (noteId: number) => {
        setSelectedNoteId(noteId);
        setIsEditing(false);
        setInitialTags([]);
    };

    const handleNoteDeleted = () => {
        setSelectedNoteId(null);
        setIsEditing(false);
        setInitialTags([]);
    };

    const handleFolderChange = (folder: string) => {
        setSelectedFolder(folder);
        setSelectedTag(null);
    };

    const handleTagClick = (tag: string) => {
        setSelectedTag(tag);
        setSelectedFolder('all');
    };

    // Check if we should show the Daily Tracker
    const showDailyTracker = selectedFolder === 'daily-tracker' || selectedFolder === 'health-log';

    return (
        <div className="flex h-screen bg-[#121212] text-white overflow-hidden">
            {/* A. Left Pane - Sidebar */}
            <Sidebar
                selectedFolder={selectedFolder}
                selectedTag={selectedTag}
                onFolderChange={handleFolderChange}
                onTagClick={handleTagClick}
                onNewNote={handleNewNote}
                isCollapsed={isSidebarCollapsed}
                onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            />

            {/* Conditional rendering based on selectedFolder */}
            {showDailyTracker ? (
                <DailyTracker initialTab={selectedFolder === 'health-log' ? 'reports' : 'today'} />
            ) : (
                <>
                    {/* B. Feed - Notes List (~320px) */}
                    <NotesFeed
                        selectedFolder={selectedFolder}
                        selectedTag={selectedTag}
                        selectedNoteId={selectedNoteId}
                        onNoteSelect={handleNoteSelect}
                    />

                    {/* C. Editor - Note Content (remaining width) */}
                    <NoteEditor
                        noteId={selectedNoteId}
                        isEditing={isEditing}
                        onEditToggle={() => setIsEditing(!isEditing)}
                        onNoteCreated={handleNoteCreated}
                        onNoteDeleted={handleNoteDeleted}
                        initialTags={initialTags}
                        onNewNoteWithTags={handleNewNoteWithTags}
                    />
                </>
            )}
        </div>
    );
}


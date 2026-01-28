import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import { TextStyle } from '@tiptap/extension-text-style';
import { Color } from '@tiptap/extension-color';
import { useEffect, useCallback } from 'react';

interface RichTextEditorProps {
    content: string;
    onChange: (html: string) => void;
    placeholder?: string;
    editable?: boolean;
}

const MenuBar = ({ editor }: { editor: ReturnType<typeof useEditor> }) => {
    if (!editor) {
        return null;
    }

    return (
        <div className="flex flex-wrap gap-1 p-2 border-b border-gray-300 bg-gray-50">
            {/* Text formatting */}
            <button
                type="button"
                onClick={() => editor.chain().focus().toggleBold().run()}
                className={`px-2 py-1 rounded text-sm font-medium transition-colors ${editor.isActive('bold') ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                    }`}
                title="Bold"
            >
                B
            </button>
            <button
                type="button"
                onClick={() => editor.chain().focus().toggleItalic().run()}
                className={`px-2 py-1 rounded text-sm italic transition-colors ${editor.isActive('italic') ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                    }`}
                title="Italic"
            >
                I
            </button>
            <button
                type="button"
                onClick={() => editor.chain().focus().toggleUnderline().run()}
                className={`px-2 py-1 rounded text-sm underline transition-colors ${editor.isActive('underline') ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                    }`}
                title="Underline"
            >
                U
            </button>
            <button
                type="button"
                onClick={() => editor.chain().focus().toggleStrike().run()}
                className={`px-2 py-1 rounded text-sm line-through transition-colors ${editor.isActive('strike') ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                    }`}
                title="Strikethrough"
            >
                S
            </button>

            <div className="w-px h-6 bg-gray-300 mx-1 self-center" />

            {/* Headings */}
            <select
                onChange={(e) => {
                    const value = e.target.value;
                    if (value === 'p') {
                        editor.chain().focus().setParagraph().run();
                    } else {
                        editor.chain().focus().toggleHeading({ level: parseInt(value) as 1 | 2 | 3 }).run();
                    }
                }}
                value={
                    editor.isActive('heading', { level: 1 }) ? '1' :
                        editor.isActive('heading', { level: 2 }) ? '2' :
                            editor.isActive('heading', { level: 3 }) ? '3' : 'p'
                }
                className="px-2 py-1 rounded text-sm bg-white border border-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
                <option value="p">Normal</option>
                <option value="1">Heading 1</option>
                <option value="2">Heading 2</option>
                <option value="3">Heading 3</option>
            </select>

            <div className="w-px h-6 bg-gray-300 mx-1 self-center" />

            {/* Lists */}
            <button
                type="button"
                onClick={() => editor.chain().focus().toggleBulletList().run()}
                className={`px-2 py-1 rounded text-sm transition-colors ${editor.isActive('bulletList') ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                    }`}
                title="Bullet List"
            >
                •
            </button>
            <button
                type="button"
                onClick={() => editor.chain().focus().toggleOrderedList().run()}
                className={`px-2 py-1 rounded text-sm transition-colors ${editor.isActive('orderedList') ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                    }`}
                title="Numbered List"
            >
                1.
            </button>

            <div className="w-px h-6 bg-gray-300 mx-1 self-center" />

            {/* Colors */}
            <input
                type="color"
                onChange={(e) => editor.chain().focus().setColor(e.target.value).run()}
                value={editor.getAttributes('textStyle').color || '#000000'}
                className="w-8 h-6 rounded cursor-pointer"
                title="Text Color"
            />

            <div className="w-px h-6 bg-gray-300 mx-1 self-center" />

            {/* Link */}
            <button
                type="button"
                onClick={() => {
                    const url = window.prompt('Enter URL:');
                    if (url) {
                        editor.chain().focus().setLink({ href: url }).run();
                    }
                }}
                className={`px-2 py-1 rounded text-sm transition-colors ${editor.isActive('link') ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                    }`}
                title="Add Link"
            >
                🔗
            </button>

            {/* Clear formatting */}
            <button
                type="button"
                onClick={() => editor.chain().focus().unsetAllMarks().clearNodes().run()}
                className="px-2 py-1 rounded text-sm bg-white text-gray-700 hover:bg-gray-100 transition-colors"
                title="Clear Formatting"
            >
                ✕
            </button>
        </div>
    );
};

export default function RichTextEditor({
    content,
    onChange,
    placeholder = 'Start writing...',
    editable = true,
    className = ''
}: RichTextEditorProps & { className?: string }) {
    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                heading: {
                    levels: [1, 2, 3],
                },
            }),
            Underline,
            TextStyle,
            Color,
            Link.configure({
                openOnClick: false,
            }),
            Placeholder.configure({
                placeholder,
            }),
        ],
        content: content || '',
        editable,
        onUpdate: ({ editor }) => {
            onChange(editor.getHTML());
        },
        // Prevent clipboard content from being auto-pasted on creation
        editorProps: {
            attributes: {
                class: `tiptap prose prose-sm max-w-none focus:outline-none p-4 ${editable ? 'min-h-[200px]' : ''} ${className}`,
            },
        },
    });

    // Update content when prop changes (for editing existing notes)
    useEffect(() => {
        if (editor && content !== editor.getHTML()) {
            editor.commands.setContent(content || '');
        }
    }, [content, editor]);

    // Update editable state
    useEffect(() => {
        if (editor) {
            editor.setEditable(editable);
        }
    }, [editable, editor]);

    if (!editor) {
        return (
            <div className="bg-white rounded-lg border border-gray-300 min-h-[300px] flex items-center justify-center">
                <span className="text-gray-400">Loading editor...</span>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg border border-gray-300 overflow-hidden">
            {editable && <MenuBar editor={editor} />}
            <EditorContent editor={editor} />
        </div>
    );
}

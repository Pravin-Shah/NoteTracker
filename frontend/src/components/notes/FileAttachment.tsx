import { Download, FileText, FileSpreadsheet, FileImage, File, Archive, Code } from 'lucide-react';
import type { Attachment } from '../../types/note';

interface FileAttachmentProps {
    attachment: Attachment;
    onDelete?: () => void;
    showDelete?: boolean;
}

const getFileIcon = (fileType: string | null, filename: string | null) => {
    const ext = filename?.split('.').pop()?.toLowerCase() || '';

    if (fileType === 'image') {
        return <FileImage className="w-5 h-5" />;
    }

    // Documents
    if (['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'].includes(ext)) {
        return <FileText className="w-5 h-5" />;
    }

    // Spreadsheets
    if (['xls', 'xlsx', 'csv', 'ods'].includes(ext)) {
        return <FileSpreadsheet className="w-5 h-5" />;
    }

    // Archives
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
        return <Archive className="w-5 h-5" />;
    }

    // Code
    if (['py', 'js', 'html', 'css', 'json', 'xml', 'md'].includes(ext)) {
        return <Code className="w-5 h-5" />;
    }

    return <File className="w-5 h-5" />;
};

const formatFileSize = (bytes: number | null | undefined): string => {
    if (!bytes) return 'Unknown size';

    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const getDisplayFilename = (attachment: Attachment): string => {
    // Try original_filename first, then fall back to file_path
    return attachment.original_filename || attachment.file_path || 'Untitled file';
};

export default function FileAttachment({ attachment, onDelete, showDelete = false }: FileAttachmentProps) {
    const displayFilename = getDisplayFilename(attachment);

    const handleDownload = () => {
        const link = document.createElement('a');
        link.href = `/uploads/${attachment.file_path}`;
        link.download = displayFilename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleOpen = () => {
        window.open(`/uploads/${attachment.file_path}`, '_blank');
    };

    return (
        <div className="group relative flex items-center gap-3 p-3 bg-[#2a2a2a] border border-gray-700 rounded-lg hover:bg-[#333] transition-colors">
            {/* File Icon */}
            <div className="flex-shrink-0 text-blue-400">
                {getFileIcon(attachment.file_type, displayFilename)}
            </div>

            {/* File Info */}
            <div className="flex-1 min-w-0">
                <div className="text-sm text-gray-200 truncate">
                    {displayFilename}
                </div>
                <div className="text-xs text-gray-500">
                    {formatFileSize(attachment.file_size)}
                    {attachment.upload_date && (
                        <span className="ml-2">
                            • {new Date(attachment.upload_date).toLocaleDateString()}
                        </span>
                    )}
                </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
                <button
                    onClick={handleOpen}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded transition-colors"
                    title="Open file"
                >
                    Open
                </button>
                <button
                    onClick={handleDownload}
                    className="p-1.5 bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors"
                    title="Download file"
                >
                    <Download className="w-4 h-4" />
                </button>
                {showDelete && onDelete && (
                    <button
                        onClick={onDelete}
                        className="p-1.5 bg-red-600 hover:bg-red-500 text-white rounded transition-colors opacity-0 group-hover:opacity-100"
                        title="Delete file"
                    >
                        ×
                    </button>
                )}
            </div>
        </div>
    );
}

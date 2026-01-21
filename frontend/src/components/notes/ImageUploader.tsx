import { useState, useRef, useCallback } from 'react';

interface ImageUploaderProps {
    onImagesChange: (files: File[]) => void;
}

export default function ImageUploader({ onImagesChange }: ImageUploaderProps) {
    const [images, setImages] = useState<File[]>([]);
    const [previews, setPreviews] = useState<string[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const pasteAreaRef = useRef<HTMLDivElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);
        addImages(files);
    };

    const handlePaste = useCallback((e: ClipboardEvent) => {
        const items = e.clipboardData?.items;
        if (!items) return;

        const files: File[] = [];
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                const file = items[i].getAsFile();
                if (file) files.push(file);
            }
        }

        if (files.length > 0) {
            e.preventDefault();
            addImages(files);
        }
    }, []);

    const addImages = (newFiles: File[]) => {
        const imageFiles = newFiles.filter((file) =>
            file.type.startsWith('image/')
        );

        if (imageFiles.length === 0) return;

        const updatedImages = [...images, ...imageFiles];
        setImages(updatedImages);
        onImagesChange(updatedImages);

        // Generate previews
        imageFiles.forEach((file) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                setPreviews((prev) => [...prev, reader.result as string]);
            };
            reader.readAsDataURL(file);
        });
    };

    const removeImage = (index: number) => {
        const updatedImages = images.filter((_, i) => i !== index);
        const updatedPreviews = previews.filter((_, i) => i !== index);
        setImages(updatedImages);
        setPreviews(updatedPreviews);
        onImagesChange(updatedImages);
    };

    // Add paste event listener
    useState(() => {
        const pasteArea = pasteAreaRef.current;
        if (pasteArea) {
            pasteArea.addEventListener('paste', handlePaste as any);
            return () => pasteArea.removeEventListener('paste', handlePaste as any);
        }
    });

    return (
        <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">
                Images
            </label>

            {/* Paste Area */}
            <div
                ref={pasteAreaRef}
                tabIndex={0}
                className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 focus:border-blue-500 focus:outline-none cursor-pointer transition-colors"
                onClick={() => fileInputRef.current?.click()}
            >
                <div className="space-y-2">
                    <div className="text-4xl">📋</div>
                    <p className="text-sm text-gray-600">
                        Click to upload or <strong>paste images here</strong> (Ctrl+V)
                    </p>
                    <p className="text-xs text-gray-500">
                        PNG, JPG, GIF up to 10MB
                    </p>
                </div>
            </div>

            {/* Hidden File Input */}
            <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileSelect}
                className="hidden"
            />

            {/* Image Previews */}
            {previews.length > 0 && (
                <div className="grid grid-cols-3 gap-3">
                    {previews.map((preview, index) => (
                        <div key={index} className="relative group">
                            <img
                                src={preview}
                                alt={`Preview ${index + 1}`}
                                className="w-full h-32 object-cover rounded-lg border border-gray-200"
                            />
                            <button
                                type="button"
                                onClick={() => removeImage(index)}
                                className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                                title="Remove image"
                            >
                                ×
                            </button>
                            <div className="absolute bottom-1 left-1 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">
                                {(images[index].size / 1024).toFixed(0)} KB
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {images.length > 0 && (
                <p className="text-sm text-gray-600">
                    📎 {images.length} image{images.length > 1 ? 's' : ''} ready to upload
                </p>
            )}
        </div>
    );
}

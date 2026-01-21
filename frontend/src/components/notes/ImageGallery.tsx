import { useState, useEffect } from 'react';

interface ImageAttachment {
    id: number;
    file_path: string;
    file_type: string | null;
    upload_date: string | null;
}

interface ImageGalleryProps {
    images: ImageAttachment[];
    onClose: () => void;
}

export default function ImageGallery({ images, onClose }: ImageGalleryProps) {
    const [currentIndex, setCurrentIndex] = useState(0);

    const handlePrevious = () => {
        setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
    };

    const handleNext = () => {
        setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
    };

    const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose();
        if (e.key === 'ArrowLeft') handlePrevious();
        if (e.key === 'ArrowRight') handleNext();
    };

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    const currentImage = images[currentIndex];

    return (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-90 flex items-center justify-center">
            {/* Close Button */}
            <button
                onClick={onClose}
                className="absolute top-4 right-4 text-white text-3xl hover:text-gray-300 z-10"
                title="Close (Esc)"
            >
                ×
            </button>

            {/* Previous Button */}
            {images.length > 1 && (
                <button
                    onClick={handlePrevious}
                    className="absolute left-4 text-white text-4xl hover:text-gray-300 z-10"
                    title="Previous (←)"
                >
                    ‹
                </button>
            )}

            {/* Image */}
            <div className="max-w-6xl max-h-[90vh] w-full h-full flex items-center justify-center p-8">
                <img
                    src={`/uploads/${currentImage.file_path}`}
                    alt={`Image ${currentIndex + 1}`}
                    className="max-w-full max-h-full object-contain"
                />
            </div>

            {/* Next Button */}
            {images.length > 1 && (
                <button
                    onClick={handleNext}
                    className="absolute right-4 text-white text-4xl hover:text-gray-300 z-10"
                    title="Next (→)"
                >
                    ›
                </button>
            )}

            {/* Image Counter */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-white bg-black bg-opacity-50 px-4 py-2 rounded">
                {currentIndex + 1} / {images.length}
            </div>

            {/* Thumbnail Strip */}
            {images.length > 1 && (
                <div className="absolute bottom-16 left-1/2 transform -translate-x-1/2 flex gap-2 overflow-x-auto max-w-[90vw] p-2">
                    {images.map((img, idx) => (
                        <button
                            key={img.id}
                            onClick={() => setCurrentIndex(idx)}
                            className={`flex-shrink-0 w-16 h-16 rounded overflow-hidden border-2 ${idx === currentIndex ? 'border-white' : 'border-transparent opacity-60'
                                } hover:opacity-100 transition-opacity`}
                        >
                            <img
                                src={`/uploads/${img.file_path}`}
                                alt={`Thumbnail ${idx + 1}`}
                                className="w-full h-full object-cover"
                            />
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

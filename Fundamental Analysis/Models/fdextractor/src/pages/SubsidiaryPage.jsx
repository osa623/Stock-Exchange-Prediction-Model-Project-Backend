import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    BuildingLibraryIcon,
    ArrowLeftIcon,
    ArrowPathIcon,
    DocumentMagnifyingGlassIcon,
    CheckCircleIcon,
    ExclamationCircleIcon,
    PhotoIcon
} from '@heroicons/react/24/outline';
import { pdfService } from '../services/api';

const SubsidiaryPage = () => {
    const { pdfId } = useParams();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(false);
    const [detecting, setDetecting] = useState(false);
    const [detectedPages, setDetectedPages] = useState([]);
    const [pageImages, setPageImages] = useState([]);
    const [selectedPage, setSelectedPage] = useState(null);
    const [selectedImage, setSelectedImage] = useState(null);
    const [extractionResult, setExtractionResult] = useState(null);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);

    // Auto-detect on mount
    useEffect(() => {
        handleDetectPages();
    }, [pdfId]);

    const handleDetectPages = async () => {
        setDetecting(true);
        setError(null);
        setDetectedPages([]);
        setPageImages([]);

        try {
            const response = await pdfService.detectSubsidiaryPages(pdfId);
            const pages = response.pages || [];
            setDetectedPages(pages);

            if (pages.length === 0) {
                setError("No Subsidiary Chart pages detected automatically. Please check the PDF manually.");
            } else {
                await loadImages(pages);
            }
        } catch (err) {
            console.error("Detection error:", err);
            setError("Failed to detect pages. Please try again.");
        } finally {
            setDetecting(false);
        }
    };

    const loadImages = async (pages) => {
        setLoading(true);
        try {
            const pageNums = pages.map(p => p.page_num);
            const response = await pdfService.getSubsidiaryImages(pdfId, pageNums);
            setPageImages(response.images || []);

            if (response.images && response.images.length > 0) {
                setSelectedImage(response.images[0]);
                setSelectedPage(response.images[0].page_num);
            }
        } catch (err) {
            console.error("Image fetch error:", err);
            setError("Failed to load page previews.");
        } finally {
            setLoading(false);
        }
    };

    const handleExtractChart = async () => {
        if (!selectedPage) return;

        setLoading(true);
        setError(null);
        setSuccessMessage(null);
        setExtractionResult(null);

        try {
            const response = await pdfService.extractSubsidiaryChart(pdfId, selectedPage);
            setExtractionResult(response.data);
            setSuccessMessage(`Success! Chart extracted and saved to: ${response.saved_to}`);
        } catch (err) {
            console.error("Extraction error:", err);
            setError("Failed to extract chart. The page layout might be complex.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-7xl mx-auto p-4 md:p-8 animate-fade-in text-gray-800 dark:text-gray-100 min-h-screen">

            {/* Page Header */}
            <div className="flex items-center space-x-4 mb-8">
                <button
                    onClick={() => navigate('/')}
                    className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                >
                    <ArrowLeftIcon className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                </button>
                <div className="flex items-center space-x-3">
                    <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
                        <BuildingLibraryIcon className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300">
                            Subsidiary Chart Extraction
                        </h1>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            Extract hierarchical organizational charts from annual reports
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-[calc(100vh-12rem)]">

                {/* LEFT COLUMN: Controls & Page List */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-gray-100 dark:border-slate-700 flex flex-col overflow-hidden">
                    <div className="p-4 border-b border-gray-100 dark:border-slate-700 bg-gray-50 dark:bg-slate-900/50">
                        <button
                            onClick={handleDetectPages}
                            disabled={detecting}
                            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center space-x-2 font-medium disabled:opacity-50"
                        >
                            {detecting ? (
                                <ArrowPathIcon className="w-5 h-5 animate-spin" />
                            ) : (
                                <DocumentMagnifyingGlassIcon className="w-5 h-5" />
                            )}
                            <span>{detecting ? 'Scanning...' : 'Re-Scan Pages'}</span>
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                        {detectedPages.length > 0 && !detecting && (
                            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                                Detected Pages ({pageImages.length})
                            </div>
                        )}

                        {error && (
                            <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg flex items-start space-x-2">
                                <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                <span>{error}</span>
                            </div>
                        )}

                        {successMessage && (
                            <div className="p-3 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 text-sm rounded-lg flex items-start space-x-2">
                                <CheckCircleIcon className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                <span>{successMessage}</span>
                            </div>
                        )}

                        <div className="grid grid-cols-2 gap-3">
                            {pageImages.map((img, idx) => (
                                <div
                                    key={idx}
                                    onClick={() => {
                                        setSelectedImage(img);
                                        setSelectedPage(img.page_num);
                                        setExtractionResult(null); // Reset result on page change
                                    }}
                                    className={`cursor-pointer rounded-xl border-2 transition-all duration-200 overflow-hidden relative group aspect-[3/4] ${selectedPage === img.page_num
                                            ? 'border-indigo-500 ring-2 ring-indigo-200 dark:ring-indigo-900 shadow-lg scale-[1.02]'
                                            : 'border-gray-200 dark:border-slate-700 hover:border-indigo-300 hover:shadow-md'
                                        }`}
                                >
                                    <img
                                        src={`data:image/jpeg;base64,${img.image_data}`}
                                        alt={`Page ${img.page_num}`}
                                        className="w-full h-full object-cover"
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                                        <div className="absolute bottom-2 left-2 text-white text-xs font-medium">
                                            Page {img.page_num}
                                        </div>
                                    </div>
                                    {selectedPage === img.page_num && (
                                        <div className="absolute top-2 right-2 bg-indigo-600 text-white p-1 rounded-full shadow-lg">
                                            <CheckCircleIcon className="w-4 h-4" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>

                        {pageImages.length === 0 && !detecting && !error && (
                            <div className="flex flex-col items-center justify-center py-10 text-gray-400">
                                <PhotoIcon className="w-12 h-12 mb-2 opacity-30" />
                                <p className="text-sm">No chart pages found</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* RIGHT COLUMN: Preview & Extraction */}
                <div className="md:col-span-2 bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-gray-100 dark:border-slate-700 flex flex-col overflow-hidden relative">
                    {selectedImage ? (
                        <div className="flex flex-col h-full">
                            {/* Toolbar */}
                            <div className="p-4 border-b border-gray-100 dark:border-slate-700 flex justify-between items-center bg-gray-50/50 dark:bg-slate-900/30">
                                <span className="font-semibold text-gray-700 dark:text-gray-300">
                                    Page {selectedPage} Preview
                                </span>
                                <button
                                    onClick={handleExtractChart}
                                    disabled={loading}
                                    className="py-2 px-6 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-md hover:shadow-lg transition-all flex items-center space-x-2 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? (
                                        <ArrowPathIcon className="w-5 h-5 animate-spin" />
                                    ) : (
                                        <div className="flex items-center">
                                            <BuildingLibraryIcon className="w-5 h-5 mr-2" />
                                            <span>Extract Chart</span>
                                        </div>
                                    )}
                                </button>
                            </div>

                            {/* Image Container */}
                            <div className="flex-1 overflow-auto p-6 bg-gray-100 dark:bg-black/20 flex items-center justify-center">
                                <img
                                    src={`data:image/jpeg;base64,${selectedImage.image_data}`}
                                    alt="Selected Page"
                                    className="max-h-full object-contain rounded-lg shadow-2xl"
                                />
                            </div>

                            {/* Result Drawer (Bottom) */}
                            {extractionResult && (
                                <div className="h-1/3 border-t border-gray-200 dark:border-slate-700 bg-slate-900 p-4 font-mono text-xs text-green-400 overflow-auto">
                                    <div className="flex justify-between items-center mb-2 px-2">
                                        <span className="text-gray-400 uppercase tracking-widest text-[10px] font-bold">Extraction Output</span>
                                    </div>
                                    <pre>{JSON.stringify(extractionResult, null, 2)}</pre>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                            <div className="w-20 h-20 bg-gray-100 dark:bg-slate-700/50 rounded-full flex items-center justify-center mb-4">
                                <PhotoIcon className="w-10 h-10 opacity-40" />
                            </div>
                            <p className="text-lg font-medium text-gray-500 dark:text-gray-400">Select a page to extract</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SubsidiaryPage;

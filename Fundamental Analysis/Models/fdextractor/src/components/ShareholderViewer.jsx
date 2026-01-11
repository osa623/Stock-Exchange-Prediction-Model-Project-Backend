import { useState } from 'react';
import { pdfService } from '../services/api';

const ShareholderViewer = ({ pdfId }) => {
  const [detecting, setDetecting] = useState(false);
  const [detectedPages, setDetectedPages] = useState(null);
  const [selectedPage, setSelectedPage] = useState(null);
  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [error, setError] = useState(null);

  // Step 1: Detect shareholder pages using TOC
  const handleDetectPages = async () => {
    try {
      setDetecting(true);
      setError(null);
      
      const data = await pdfService.detectShareholders(pdfId);
      setDetectedPages(data);
      
      // Auto-select first page
      if (data.pages && data.pages.length > 0) {
        const firstPage = data.pages[0].page_num;
        setSelectedPage(firstPage);
        // Automatically load images for first page
        await loadImagesForPage(firstPage);
      }
      
    } catch (err) {
      setError(err.message || 'Failed to detect shareholder pages');
    } finally {
      setDetecting(false);
    }
  };

  // Step 2: Load images for selected page
  const loadImagesForPage = async (pageNum) => {
    try {
      setError(null);
      setImages([]);
      setSelectedImage(null);
      setExtractedData(null);
      
      const data = await pdfService.getShareholderImages(pdfId, pageNum);
      setImages(data.images);
      
      // Auto-select first image (full page)
      if (data.images && data.images.length > 0) {
        setSelectedImage(data.images[0]);
      }
      
    } catch (err) {
      setError(err.message || 'Failed to load images');
    }
  };

  // Handle page selection
  const handlePageSelect = (pageNum) => {
    setSelectedPage(pageNum);
    loadImagesForPage(pageNum);
  };

  // Step 3: Extract table from selected image
  const handleExtractTable = async () => {
    if (!selectedPage || !selectedImage) {
      setError('Please select a page and image first');
      return;
    }
    
    try {
      setExtracting(true);
      setError(null);
      
      const bbox = selectedImage.bbox || null;
      const data = await pdfService.extractShareholderTable(pdfId, selectedPage, bbox);
      
      setExtractedData(data);
      
      if (data.success) {
        alert(`✅ Successfully extracted ${data.shareholder_count} shareholders!\n\nData saved to: ${data.saved_to}`);
      } else {
        setError('Extraction completed but no data found. Try selecting a different image.');
      }
      
    } catch (err) {
      setError(err.message || 'Failed to extract table');
    } finally {
      setExtracting(false);
    }
  };

  // Export to JSON
  const handleExportJSON = () => {
    if (!extractedData) return;
    
    const dataStr = JSON.stringify(extractedData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${pdfId}_shareholders_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-semibold text-gray-900 mb-2">
              Top 20 Shareholders Extraction
            </h2>
            <p className="text-base text-gray-500">
              Detect pages using TOC, view OCR images, and extract shareholder data
            </p>
          </div>
          
          <button
            onClick={handleDetectPages}
            disabled={detecting}
            className={`px-6 py-3 bg-black text-white rounded-lg font-medium transition-all duration-200 ${
              detecting ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-800'
            }`}
          >
            {detecting ? 'Detecting...' : 'Detect Pages'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm font-medium">{error}</p>
        </div>
      )}

      {/* Detected Pages */}
      {detectedPages && detectedPages.pages && detectedPages.pages.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">
            Detected Pages ({detectedPages.pages.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {detectedPages.pages.map((page, idx) => (
              <button
                key={idx}
                onClick={() => handlePageSelect(page.page_num)}
                className={`bg-gray-50 rounded-lg p-5 border transition-all duration-200 hover:shadow-md text-left ${
                  selectedPage === page.page_num
                    ? 'border-black shadow-md ring-2 ring-gray-300'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="font-semibold text-base text-gray-900">Page {page.page_num + 1}</div>
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    selectedPage === page.page_num ? 'bg-black text-white' : 'bg-gray-200 text-gray-600'
                  }`}>
                    {selectedPage === page.page_num ? '✓' : idx + 1}
                  </span>
                </div>
                <div className="text-sm text-gray-600 mb-2">
                  Confidence: {(page.confidence * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-gray-600 mb-2">
                  Source: <span className="font-medium">{page.source}</span>
                </div>
                <div className="text-xs text-gray-500 mt-3 line-clamp-2">
                  {page.evidence}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Page Images */}
      {images.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-gray-900">
              Page Images ({images.length})
            </h3>
            <button
              onClick={handleExtractTable}
              disabled={extracting || !selectedImage}
              className={`px-6 py-3 bg-black text-white rounded-lg font-medium transition-all duration-200 ${
                extracting || !selectedImage ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-800'
              }`}
            >
              {extracting ? 'Extracting...' : 'Extract Table'}
            </button>
          </div>

          <div className="space-y-4">
            {images.map((img, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedImage(img)}
                className={`bg-gray-50 rounded-lg p-5 border cursor-pointer transition-all duration-200 hover:shadow-md ${
                  selectedImage === img
                    ? 'border-black shadow-md ring-2 ring-gray-300'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex flex-col md:flex-row items-start space-y-4 md:space-y-0 md:space-x-5">
                  <div className="flex-shrink-0">
                    <img
                      src={`data:image/png;base64,${img.image_data}`}
                      alt={img.description}
                      className="max-w-full md:max-w-md rounded-lg shadow-sm border border-gray-200"
                    />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="font-semibold text-base text-gray-900 capitalize">
                        {img.image_type.replace('_', ' ')}
                      </div>
                      {selectedImage === img && (
                        <span className="bg-black text-white text-xs px-3 py-1 rounded-full font-medium">
                          Selected
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{img.description}</p>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div>Size: {img.width} x {img.height} px</div>
                      <div>Format: {img.format.toUpperCase()}</div>
                      {img.table_index !== undefined && (
                        <div>Table Index: {img.table_index}</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extracted Data */}
      {extractedData && extractedData.success && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                Extracted Shareholders ({extractedData.shareholder_count})
              </h3>
              <p className="text-sm text-gray-500 mt-2">
                File saved to: <span className="font-mono text-xs">{extractedData.saved_to}</span>
              </p>
            </div>
            
            <button
              onClick={handleExportJSON}
              className="px-6 py-3 bg-black text-white rounded-lg font-medium transition-all duration-200 hover:bg-gray-800"
            >
              Download JSON
            </button>
          </div>

          {/* Shareholder Table */}
          <div className="bg-white rounded-lg overflow-hidden border border-gray-200">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      #
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Shareholder Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      No. of Shares
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Percentage (%)
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {extractedData.shareholders && extractedData.shareholders.map((shareholder, idx) => (
                    <tr key={idx} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {idx + 1}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {shareholder.name || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {shareholder.shares ? 
                          (typeof shareholder.shares === 'number' ? shareholder.shares.toLocaleString() : shareholder.shares) 
                          : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {shareholder.percentage || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Raw Table Preview */}
          {extractedData.raw_table && (
            <div className="mt-6">
              <details className="bg-gray-50 rounded-lg p-5 border border-gray-200">
                <summary className="cursor-pointer font-semibold text-gray-900 hover:text-gray-700 flex items-center space-x-2">
                  <span>View Raw Extraction Data</span>
                </summary>
                <div className="mt-4">
                  <div className="text-xs text-gray-600 mb-3">
                    Method: <span className="font-mono bg-white px-2 py-1 rounded border border-gray-200">{extractedData.raw_table.method}</span>
                  </div>
                  <pre className="text-xs bg-white p-4 rounded-lg border border-gray-200 overflow-auto max-h-64 font-mono">
                    {JSON.stringify(extractedData.raw_table, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          )}
        </div>
      )}

      {/* Info Box */}
      <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
        <div className="flex items-start space-x-4">
          <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center flex-shrink-0 text-white font-bold text-sm">
            i
          </div>
          <div className="text-sm text-gray-700">
            <p className="font-semibold mb-2 text-gray-900">How it works:</p>
            <ol className="list-decimal list-inside space-y-2 text-xs text-gray-600">
              <li><strong>Detect Pages:</strong> Uses TOC detector to find "Top 20 Shareholders" pages</li>
              <li><strong>View Images:</strong> Converts detected pages to high-resolution images (300 DPI)</li>
              <li><strong>Select Image:</strong> Choose full page or specific table region</li>
              <li><strong>Extract Table:</strong> Uses Camelot OCR to parse table data into structured JSON</li>
              <li><strong>Export:</strong> Download extracted data as JSON file for further processing</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShareholderViewer;

import { useState } from 'react';
import { pdfService } from '../services/api';

const InvestorRelationsViewer = ({ pdfId }) => {
  const [detecting, setDetecting] = useState(false);
  const [detectedPages, setDetectedPages] = useState(null);
  const [selectedPage, setSelectedPage] = useState(null);
  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [error, setError] = useState(null);

  // Step 1: Detect investor relations pages using TOC
  const handleDetectPages = async () => {
    try {
      setDetecting(true);
      setError(null);

      const data = await pdfService.detectInvestorRelations(pdfId);
      setDetectedPages(data);

      // Auto-load images for all detected pages
      if (data.pages && data.pages.length > 0) {
        const pageNumbers = data.pages.map(p => p.page_num);
        await loadImagesForAllPages(pageNumbers);
      }

    } catch (err) {
      setError(err.message || 'Failed to detect investor relations pages');
    } finally {
      setDetecting(false);
    }
  };

  // Step 2: Load images for all detected pages
  const loadImagesForAllPages = async (pageNumbers) => {
    try {
      setError(null);
      setImages([]);
      setSelectedImage(null);
      setExtractedData(null);

      const data = await pdfService.getInvestorRelationsImages(pdfId, pageNumbers);
      setImages(data.images);

      // Auto-select first image
      if (data.images && data.images.length > 0) {
        setSelectedImage(data.images[0]);
        setSelectedPage(data.images[0].page_num);
      }

    } catch (err) {
      setError(err.message || 'Failed to load images');
    }
  };

  const handlePageSelect = (pageNum) => {
    setSelectedPage(pageNum);
  };

  // Step 3: Extract data from selected image
  const handleExtractData = async () => {
    if (!selectedImage) {
      setError('Please select a page and image first');
      return;
    }

    try {
      setExtracting(true);
      setError(null);

      const bbox = selectedImage.bbox || null;
      // Use the page_num from the selected image to ensure sync
      const pageNum = selectedImage.page_num || selectedPage;

      const data = await pdfService.extractInvestorRelationsData(pdfId, pageNum, bbox);

      setExtractedData(data);

      if (data.success) {
        alert(`✅ Successfully extracted investor relations data!\\n\\nData saved to: ${data.saved_to}`);
      } else {
        setError('Extraction completed but no data found. Try selecting a different image.');
      }

    } catch (err) {
      setError(err.message || 'Failed to extract data');
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
    link.download = `${pdfId}_investor_relations_${Date.now()}.json`;
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
              Investor Relations Extraction
            </h2>
            <p className="text-base text-gray-500">
              Detect pages using content analysis and extract investor relations data
            </p>
          </div>

          <button
            onClick={handleDetectPages}
            disabled={detecting}
            className={`px-6 py-3 bg-black text-white rounded-lg font-medium transition-all duration-200 ${detecting ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-800'
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

      {/* Detected Pages - Categorical View */}
      {detectedPages && detectedPages.pages && detectedPages.pages.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">
            Detected Pages ({detectedPages.pages.length})
          </h3>

          <div className="space-y-4">
            {detectedPages.pages.map((page, idx) => (
              <div
                key={idx}
                className="bg-gray-50 rounded-lg p-5 border border-gray-200 hover:border-gray-300 transition-all duration-200"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4 mb-3">
                      <div>
                        <div className="text-lg font-semibold text-gray-900">Page {page.page_num}</div>
                        <div className="text-sm text-gray-500 mt-1">
                          Confidence: {(page.confidence * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600 mb-2">
                        <span className="font-medium">Source:</span> {page.source}
                      </div>
                      <div className="text-sm text-gray-700 bg-white p-3 rounded border border-gray-200">
                        {page.evidence}
                      </div>
                    </div>
                  </div>

                  <div className="ml-6">
                    <span className={`px-4 py-2 rounded-lg text-xs font-medium ${page.type === 'shareholders_page'
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-200 text-gray-700'
                      }`}>
                      {page.type === 'shareholders_page' ? 'Shareholder Data' : 'Investor Relations'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Page Images - Categorical View by Page */}
      {images.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-xl font-semibold text-gray-900">
              Page Previews - {images.length} Page{images.length > 1 ? 's' : ''}
            </h3>
            <button
              onClick={handleExtractData}
              disabled={extracting || !selectedImage}
              className={`px-6 py-3 bg-black text-white rounded-lg font-medium transition-all duration-200 ${extracting || !selectedImage ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-800'
                }`}
            >
              {extracting ? 'Extracting...' : 'Extract Selected Page'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {images.map((image, idx) => (
              <div key={idx} className="bg-white rounded-lg overflow-hidden border border-gray-200 hover:shadow-md transition-shadow duration-200 flex flex-col">
                {/* Page Header */}
                <div className="bg-white border-b border-gray-100 px-4 py-3 flex items-center justify-between">
                  <h4 className="font-semibold text-gray-900 text-sm">Page {image.page_num}</h4>
                  <button
                    onClick={() => { setSelectedImage(image); setSelectedPage(image.page_num); }}
                    className={`px-3 py-1 rounded text-xs font-medium transition-colors duration-200 ${selectedImage === image
                      ? 'bg-black text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                  >
                    {selectedImage === image ? 'Selected' : 'Select'}
                  </button>
                </div>

                {/* Image Preview */}
                <div
                  onClick={() => { setSelectedImage(image); setSelectedPage(image.page_num); }}
                  className={`cursor-pointer p-2 flex-grow flex items-center justify-center bg-gray-50 transition-colors duration-200 ${selectedImage === image ? 'bg-gray-100 ring-2 ring-inset ring-black' : 'hover:bg-gray-100'
                    }`}
                >
                  <img
                    src={`data:image/png;base64,${image.image_data}`}
                    alt={`Page ${image.page_num}`}
                    className="max-w-full max-h-64 object-contain shadow-sm"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extracted Data */}
      {extractedData && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                Extracted Data
              </h3>
              {extractedData.attribute_count && (
                <p className="text-sm text-gray-500 mt-1">
                  {extractedData.attribute_count} attributes extracted
                </p>
              )}
            </div>
            <button
              onClick={handleExportJSON}
              className="px-6 py-3 bg-black text-white rounded-lg font-medium transition-all duration-200 hover:bg-gray-800"
            >
              Download JSON
            </button>
          </div>

          {/* Display structured data if available */}
          {extractedData.data && typeof extractedData.data === 'object' && Object.keys(extractedData.data).length > 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sticky left-0 bg-gray-50">
                        Attribute
                      </th>
                      {/* Extract all unique years from the data */}
                      {Object.values(extractedData.data)[0] &&
                        Object.keys(Object.values(extractedData.data)[0]).map((year, idx) => (
                          <th key={idx} className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                            {year}
                          </th>
                        ))
                      }
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {Object.entries(extractedData.data).map(([attribute, yearValues], idx) => (
                      <tr key={idx} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                          {attribute}
                        </td>
                        {Object.values(yearValues).map((value, valueIdx) => (
                          <td key={valueIdx} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {value}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            /* Fallback to JSON view if data format is different */
            <div className="bg-gray-50 rounded-lg p-5 max-h-96 overflow-y-auto border border-gray-200">
              <pre className="text-xs text-gray-800 whitespace-pre-wrap font-mono">
                {JSON.stringify(extractedData, null, 2)}
              </pre>
            </div>
          )}

          {/* Raw table info */}
          {extractedData.raw_table && (
            <div className="mt-6">
              <details className="bg-gray-50 rounded-lg p-5 border border-gray-200">
                <summary className="cursor-pointer font-semibold text-gray-900 hover:text-gray-700 flex items-center space-x-2">
                  <span>View Raw Extraction Details</span>
                </summary>
                <div className="mt-4">
                  <div className="text-xs text-gray-600 space-y-2">
                    <div>Extraction Method: <span className="font-mono bg-white px-2 py-1 rounded border border-gray-200">{extractedData.raw_table.method}</span></div>
                    <div>Rows: {extractedData.raw_table.rows}</div>
                    <div>Columns: {extractedData.raw_table.columns}</div>
                  </div>
                </div>
              </details>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default InvestorRelationsViewer;

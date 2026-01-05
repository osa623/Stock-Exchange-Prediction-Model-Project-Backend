import React, { useState } from 'react';

const StatementCard = ({ statement, isSelected, onToggleSelect, selectedImage, onImageSelect, selectedPages = [], onPageSelect }) => {
  const { type, data, confidence, images = [] } = statement;
  const [showImages, setShowImages] = useState(images.length > 0);

  const getStatementTitle = (type) => {
    const titles = {
      income: 'Income Statement',
      balance: 'Balance Sheet',
      cashflow: 'Cash Flow Statement',
    };
    return titles[type] || type;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const isPageSelected = (pageNum) => {
    return selectedPages.includes(pageNum);
  };

  const handlePageCheckboxClick = (e, pageNum) => {
    e.stopPropagation(); // Prevent triggering image selection
    if (onPageSelect) {
      onPageSelect(type, pageNum);
    }
  };

  return (
    <div
      className={`card p-6 transition-all ${
        isSelected ? 'border-black border-2' : ''
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-bold mb-2">{getStatementTitle(type)}</h3>
          {confidence !== undefined && (
            <p className={`text-sm font-medium ${getConfidenceColor(confidence)}`}>
              Confidence: {(confidence * 100).toFixed(1)}%
            </p>
          )}
        </div>
        <div
          className={`w-6 h-6 border-2 rounded flex items-center justify-center cursor-pointer ${
            isSelected ? 'bg-black border-black' : 'border-gray-400'
          }`}
          onClick={onToggleSelect}
        >
          {isSelected && (
            <svg
              className="w-4 h-4 text-white"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M5 13l4 4L19 7"></path>
            </svg>
          )}
        </div>
      </div>

      {/* Statement Images */}
      {images && images.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-gray-700">
              Statement Images ({images.length})
            </h4>
            <button
              onClick={() => setShowImages(!showImages)}
              className="text-xs text-gray-600 hover:text-black"
            >
              {showImages ? 'Hide' : 'Show'}
            </button>
          </div>
          
          {showImages && (
            <div className="grid grid-cols-1 gap-3">
              {images.map((image, idx) => (
                <div
                  key={idx}
                  className={`relative border-2 rounded cursor-pointer transition-all ${
                    selectedImage === image.url
                      ? 'border-black shadow-md'
                      : 'border-gray-200 hover:border-gray-400'
                  }`}
                  onClick={() => onImageSelect(type, image.url)}
                >
                  {/* Page Selection Checkbox */}
                  <div 
                    className="absolute top-2 left-2 z-10"
                    onClick={(e) => handlePageCheckboxClick(e, image.page)}
                  >
                    <div
                      className={`w-6 h-6 border-2 rounded flex items-center justify-center cursor-pointer transition-all ${
                        isPageSelected(image.page) 
                          ? 'bg-black border-black' 
                          : 'bg-white border-gray-400 hover:border-black'
                      }`}
                    >
                      {isPageSelected(image.page) && (
                        <svg
                          className="w-4 h-4 text-white"
                          fill="none"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path d="M5 13l4 4L19 7"></path>
                        </svg>
                      )}
                    </div>
                  </div>
                  
                  <img
                    src={image.url}
                    alt={`Page ${image.page}`}
                    className="w-full h-auto rounded"
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="%23f0f0f0"/><text x="50" y="50" text-anchor="middle" fill="%23999">No Image</text></svg>';
                    }}
                  />
                  <div className="absolute top-2 right-2 bg-black text-white px-2 py-1 rounded text-xs">
                    Page {image.page}
                  </div>
                  {selectedImage === image.url && (
                    <div className="absolute bottom-2 left-2 bg-black text-white p-1 rounded-full">
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path d="M5 13l4 4L19 7"></path>
                      </svg>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Statement Data Preview */}
      <div className="bg-gray-50 rounded p-4 max-h-64 overflow-y-auto">
        {data && typeof data === 'object' ? (
          <div className="space-y-2">
            {Object.entries(data).slice(0, 10).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm border-b border-gray-200 pb-1">
                <span className="font-medium text-gray-700">{key}:</span>
                <span className="text-gray-900">{value}</span>
              </div>
            ))}
            {Object.entries(data).length > 10 && (
              <p className="text-xs text-gray-500 text-center mt-2">
                + {Object.entries(data).length - 10} more items
              </p>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-600">
            {data || 'No data available'}
          </p>
        )}
      </div>

      {/* Statement Metadata */}
      {statement.pages && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-600">
            <span className="font-medium">Source Pages:</span> {statement.pages}
          </p>
        </div>
      )}
    </div>
  );
};

export default StatementCard;

import React from 'react';
import { useNavigate } from 'react-router-dom';

const PDFCard = ({ pdf }) => {
  const navigate = useNavigate();

  const handleExtraction = (type) => {
    if (type === 'statements') {
      navigate(`/pdf/${pdf.id}/statements`);
    } else if (type === 'company') {
      navigate(`/pdf/${pdf.id}/company`);
    } else if (type === 'other') {
      navigate(`/pdf/${pdf.id}/other`);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden border border-gray-200 flex flex-col h-full">
      {/* PDF Header with gradient */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4">
        <h3 className="font-bold text-lg text-white mb-1 truncate">{pdf.name}</h3>
        <div className="flex items-center space-x-2">
          <span className="bg-white/20 backdrop-blur-sm px-2 py-1 rounded text-xs text-white">
            {pdf.category || 'Uncategorized'}
          </span>
        </div>
      </div>

      {/* PDF Information */}
      <div className="p-4 space-y-2 flex-grow">
        <div className="flex items-center text-sm">
          <span className="text-gray-500 w-20">Company:</span>
          <span className="text-gray-900 font-medium">{pdf.company || 'N/A'}</span>
        </div>
        <div className="flex items-center text-sm">
          <span className="text-gray-500 w-20">Year:</span>
          <span className="text-gray-900 font-medium">{pdf.year || 'N/A'}</span>
        </div>
        {pdf.pages && (
          <div className="flex items-center text-sm">
            <span className="text-gray-500 w-20">Pages:</span>
            <span className="text-gray-900 font-medium">{pdf.pages}</span>
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="border-t border-gray-200"></div>

      {/* Action Buttons */}
      <div className="p-4 space-y-2 bg-gray-50">
        <p className="text-xs text-gray-600 font-medium mb-3 uppercase tracking-wide">
          Select Extraction Type
        </p>
        
        {/* Button 1: Financial Statements */}
        <button
          onClick={() => handleExtraction('statements')}
          className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white px-4 py-3 rounded-lg text-sm font-semibold transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5 flex items-center justify-between"
        >
          <span>📊 Financial Statements</span>
          <span className="text-xs bg-white/20 px-2 py-1 rounded">→</span>
        </button>

        {/* Button 2: Company Details */}
        <button
          onClick={() => handleExtraction('company')}
          className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-3 rounded-lg text-sm font-semibold transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5 flex items-center justify-between"
        >
          <span>🏢 Company Details</span>
          <span className="text-xs bg-white/20 px-2 py-1 rounded">→</span>
        </button>

        {/* Button 3: Other Extraction */}
        <button
          onClick={() => handleExtraction('other')}
          className="w-full bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white px-4 py-3 rounded-lg text-sm font-semibold transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5 flex items-center justify-between"
        >
          <span>⚙️ Other Data</span>
          <span className="text-xs bg-white/20 px-2 py-1 rounded">→</span>
        </button>
      </div>
    </div>
  );
};

export default PDFCard;

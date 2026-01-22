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
    <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden border border-gray-200 flex flex-col h-full">
      {/* PDF Header */}
      <div className="bg-gray-50 border-b border-gray-200 p-5">
        <h3 className="font-semibold text-base text-gray-900 mb-2 truncate">{pdf.name}</h3>
        <div className="flex items-center space-x-2">
          <span className="bg-gray-200 px-3 py-1 rounded text-xs text-gray-700 font-medium">
            {pdf.category || 'Uncategorized'}
          </span>
        </div>
      </div>

      {/* PDF Information */}
      <div className="p-5 space-y-2 flex-grow">
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
      <div className="p-5 space-y-2 bg-gray-50">
        <p className="text-xs text-gray-500 font-medium mb-3 uppercase tracking-wide">
          Select Extraction Type
        </p>

        {/* Button 1: Financial Statements */}
        <button
          onClick={() => handleExtraction('statements')}
          className="w-full bg-black hover:bg-gray-800 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
        >
          Financial Statements
        </button>

        {/* Button 2: Company Details */}
        <button
          onClick={() => handleExtraction('company')}
          className="w-full bg-gray-200 hover:bg-gray-300 text-gray-900 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
        >
          Company Details
        </button>

        {/* Button 3: Other Extraction */}
        <button
          onClick={() => handleExtraction('other')}
          className="w-full bg-gray-200 hover:bg-gray-300 text-gray-900 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
        >
          Other Data
        </button>


        {/* Button 4: Investor Relations */}
        <button
          onClick={() => navigate(`/pdf/${pdf.id}/investor-relations`)}
          className="w-full bg-gray-200 hover:bg-gray-300 text-gray-900 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
        >
          Top 10 ShareHolders
        </button>

        {/* Button 5: Subsidiaries */}
        <button
          onClick={() => navigate(`/pdf/${pdf.id}/subsidiary`)}
          className="w-full bg-indigo-100 hover:bg-indigo-200 text-indigo-900 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 flex items-center justify-center space-x-2"
        >
          <span>Subsidiaries Chart</span>
        </button>
      </div>
    </div>
  );
};

export default PDFCard;

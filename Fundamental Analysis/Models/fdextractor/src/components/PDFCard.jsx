import React from 'react';
import { useNavigate } from 'react-router-dom';

const PDFCard = ({ pdf }) => {
  const navigate = useNavigate();

  const handleSelect = () => {
    navigate(`/pdf/${pdf.id}`);
  };

  return (
    <div className="card p-6 cursor-pointer" onClick={handleSelect}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-semibold text-lg mb-2">{pdf.name}</h3>
          <div className="space-y-1">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Company:</span> {pdf.company || 'N/A'}
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-medium">Year:</span> {pdf.year || 'N/A'}
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-medium">Category:</span> {pdf.category || 'Uncategorized'}
            </p>
            {pdf.pages && (
              <p className="text-sm text-gray-600">
                <span className="font-medium">Pages:</span> {pdf.pages}
              </p>
            )}
          </div>
        </div>
        <div className="ml-4">
          <button className="bg-black text-white px-4 py-2 rounded text-sm hover:bg-gray-800 transition-colors">
            Extract
          </button>
        </div>
      </div>
    </div>
  );
};

export default PDFCard;

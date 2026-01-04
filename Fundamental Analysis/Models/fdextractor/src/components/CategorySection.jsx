import React, { useState } from 'react';
import PDFCard from './PDFCard';

const CategorySection = ({ category, pdfs }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="mb-8">
      <div
        className="flex items-center justify-between mb-4 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h2 className="text-2xl font-bold">{category}</h2>
        <div className="flex items-center space-x-4">
          <span className="bg-black text-white px-3 py-1 rounded-full text-sm font-medium">
            {pdfs.length} {pdfs.length === 1 ? 'PDF' : 'PDFs'}
          </span>
          <button className="text-2xl font-bold transition-transform duration-200" style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>
            ▼
          </button>
        </div>
      </div>
      
      {isExpanded && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {pdfs.map((pdf) => (
            <PDFCard key={pdf.id} pdf={pdf} />
          ))}
        </div>
      )}
    </div>
  );
};

export default CategorySection;

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { pdfService } from '../services/api';
import StatementCard from '../components/StatementCard';
import Loader from '../components/Loader';
import ErrorMessage from '../components/ErrorMessage';

const PDFDetail = () => {
  const { pdfId } = useParams();
  const navigate = useNavigate();
  
  const [pdf, setPdf] = useState(null);
  const [statements, setStatements] = useState([]);
  const [selectedStatements, setSelectedStatements] = useState(new Set());
  const [selectedImages, setSelectedImages] = useState({}); // Track selected image per statement
  const [selectedPages, setSelectedPages] = useState({}); // Track selected pages per statement type
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    extractStatements();
  }, [pdfId]);

  const extractStatements = async () => {
    try {
      setLoading(true);
      setExtracting(true);
      setError(null);
      
      const result = await pdfService.extractStatements(pdfId);
      setPdf(result.pdf);
      setStatements(result.statements || []);
    } catch (err) {
      setError(err.message || 'Failed to extract statements');
    } finally {
      setLoading(false);
      setExtracting(false);
    }
  };

  const toggleStatementSelection = (index) => {
    setSelectedStatements((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const handleImageSelect = (statementType, imageUrl) => {
    setSelectedImages((prev) => ({
      ...prev,
      [statementType]: imageUrl
    }));
  };

  const handlePageSelect = (statementType, pageNum) => {
    setSelectedPages((prev) => {
      const currentPages = prev[statementType] || [];
      const newPages = currentPages.includes(pageNum)
        ? currentPages.filter(p => p !== pageNum)
        : [...currentPages, pageNum];
      
      return {
        ...prev,
        [statementType]: newPages
      };
    });
  };

  const handleExtractData = async () => {
    // Check if any pages are selected
    const totalSelectedPages = Object.values(selectedPages).reduce(
      (sum, pages) => sum + (pages?.length || 0), 
      0
    );

    if (totalSelectedPages === 0) {
      alert('Please select at least one page to extract data from');
      return;
    }

    try {
      setExtracting(true);
      setError(null);
      
      const result = await pdfService.extractDataFromPages(pdfId, selectedPages);
      
      // Build detailed summary message
      const summary = result.extraction_summary || {};
      let summaryText = 'Data extracted successfully!\n\n';
      
      summaryText += '📊 Extraction Summary:\n';
      summaryText += `Bank Year1: ${summary.Bank?.Year1 || 0} fields\n`;
      summaryText += `Bank Year2: ${summary.Bank?.Year2 || 0} fields\n`;
      summaryText += `Group Year1: ${summary.Group?.Year1 || 0} fields\n`;
      summaryText += `Group Year2: ${summary.Group?.Year2 || 0} fields\n\n`;
      
      summaryText += `📁 Output Files:\n`;
      summaryText += `JSON: ${result.json_file}\n`;
      summaryText += `Excel: ${result.excel_file}\n\n`;
      
      summaryText += `📂 Location: ${result.output_dir}`;
      
      alert(summaryText);
      
    } catch (err) {
      setError(err.message || 'Failed to extract data');
      alert('Error extracting data: ' + (err.message || 'Unknown error'));
    } finally {
      setExtracting(false);
    }
  };

  const handleSubmit = async () => {
    if (selectedStatements.size === 0) {
      alert('Please select at least one statement');
      return;
    }

    try {
      setSubmitting(true);
      const selected = Array.from(selectedStatements).map((index) => ({
        ...statements[index],
        selectedImage: selectedImages[statements[index].type]
      }));
      await pdfService.submitSelectedStatements(pdfId, selected);
      alert('Statements submitted successfully!');
      navigate('/');
    } catch (err) {
      alert(err.message || 'Failed to submit statements');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Loader message={extracting ? 'Extracting statements...' : 'Loading...'} />
    );
  }

  if (error) {
    return (
      <ErrorMessage
        message={error}
        onRetry={() => {
          setError(null);
          extractStatements();
        }}
      />
    );
  }

  return (
    <div className="container mx-auto px-6 py-8">
      {/* Back Button */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center space-x-2 text-gray-600 hover:text-black mb-6 transition-colors"
      >
        <span className="text-xl">←</span>
        <span>Back to Dashboard</span>
      </button>

      {/* PDF Info Header */}
      {pdf && (
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">{pdf.name}</h1>
          <div className="flex items-center space-x-6 text-gray-600">
            {pdf.company && <span>Company: {pdf.company}</span>}
            {pdf.year && <span>Year: {pdf.year}</span>}
            {pdf.category && <span>Category: {pdf.category}</span>}
          </div>
        </div>
      )}

      {/* Extraction Status */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-1">
              Extracted Statements: {statements.length}
            </h2>
            <p className="text-gray-600 text-sm">
              Select pages from statements to extract data
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-gray-600 text-sm">
                {Object.values(selectedPages).reduce((sum, pages) => sum + (pages?.length || 0), 0)} pages selected
              </div>
              <div className="text-gray-500 text-xs">
                {selectedStatements.size} statements marked
              </div>
            </div>
            <button
              onClick={handleExtractData}
              disabled={Object.values(selectedPages).reduce((sum, pages) => sum + (pages?.length || 0), 0) === 0 || extracting}
              className={`btn-primary ${
                Object.values(selectedPages).reduce((sum, pages) => sum + (pages?.length || 0), 0) === 0 || extracting
                  ? 'opacity-50 cursor-not-allowed'
                  : ''
              }`}
            >
              {extracting ? 'Extracting...' : 'Extract Data'}
            </button>
            <button
              onClick={handleSubmit}
              disabled={selectedStatements.size === 0 || submitting}
              className={`btn-secondary ${
                selectedStatements.size === 0 || submitting
                  ? 'opacity-50 cursor-not-allowed'
                  : ''
              }`}
            >
              {submitting ? 'Submitting...' : 'Submit Selected'}
            </button>
          </div>
        </div>
      </div>

      {/* Statements Grid */}
      {statements.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600 text-lg">No statements extracted</p>
          <button onClick={extractStatements} className="btn-secondary mt-4">
            Retry Extraction
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {statements.map((statement, index) => (
            <StatementCard
              key={index}
              statement={statement}
              isSelected={selectedStatements.has(index)}
              onToggleSelect={() => toggleStatementSelection(index)}
              selectedImage={selectedImages[statement.type]}
              onImageSelect={handleImageSelect}
              selectedPages={selectedPages[statement.type] || []}
              onPageSelect={handlePageSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default PDFDetail;

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { pdfService } from '../services/api';
import Loader from '../components/Loader';
import ErrorMessage from '../components/ErrorMessage';

const OtherExtraction = () => {
  const { pdfId } = useParams();
  const navigate = useNavigate();

  const [pdf, setPdf] = useState(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState(null);
  const [selectedType, setSelectedType] = useState('');
  const [extractedData, setExtractedData] = useState(null);

  const extractionTypes = [
    { id: 'notes', name: 'Notes to Financial Statements', icon: '📝', color: 'from-yellow-500 to-orange-500' },
    { id: 'audit', name: 'Audit Report', icon: '✓', color: 'from-green-500 to-teal-500' },
    { id: 'governance', name: 'Corporate Governance', icon: '⚖️', color: 'from-blue-500 to-cyan-500' },
    { id: 'risk', name: 'Risk Management', icon: '⚠️', color: 'from-red-500 to-pink-500' },
    { id: 'sustainability', name: 'Sustainability Report', icon: '🌱', color: 'from-green-500 to-emerald-500' },
    { id: 'custom', name: 'Custom Extraction', icon: '🔧', color: 'from-purple-500 to-indigo-500' },
  ];

  useEffect(() => {
    loadPDFInfo();
  }, [pdfId]);

  const loadPDFInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await pdfService.extractStatements(pdfId);
      setPdf(result.pdf);
    } catch (err) {
      setError(err.message || 'Failed to load PDF information');
    } finally {
      setLoading(false);
    }
  };

  const handleExtraction = async () => {
    if (!selectedType) {
      alert('Please select an extraction type');
      return;
    }

    try {
      setExtracting(true);
      setError(null);

      // Placeholder extraction - in real implementation, this would call appropriate API
      const result = {
        type: selectedType,
        extractedAt: new Date().toISOString(),
        status: 'Success',
        pagesCovered: '12-45',
        dataPoints: 156,
        summary: `Extracted ${extractionTypes.find(t => t.id === selectedType)?.name} successfully`
      };

      setExtractedData(result);
      alert('Data extracted successfully!');
    } catch (err) {
      setError(err.message || 'Failed to extract data');
    } finally {
      setExtracting(false);
    }
  };

  if (loading) {
    return <Loader message="Loading PDF information..." />;
  }

  if (error && !pdf) {
    return <ErrorMessage message={error} onRetry={loadPDFInfo} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50">
      <div className="container mx-auto px-6 py-8">
        {/* Back Button */}
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center space-x-2 text-gray-600 hover:text-purple-600 mb-6 transition-colors group"
        >
          <span className="text-xl group-hover:-translate-x-1 transition-transform">←</span>
          <span className="font-medium">Back to Dashboard</span>
        </button>

        {/* Page Header */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 border border-gray-200">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
                  <span className="text-white text-2xl">⚙️</span>
                </div>
                <div>
                  <h1 className="text-4xl font-bold text-gray-900">Other Data Extraction</h1>
                  <p className="text-gray-600 mt-1">Extract specialized data from documents</p>
                </div>
              </div>

              {pdf && (
                <div className="flex items-center space-x-6 text-sm bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-500">📄</span>
                    <span className="font-semibold text-gray-900">{pdf.name}</span>
                  </div>
                  {pdf.company && (
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-500">Company:</span>
                      <span className="text-gray-700">{pdf.company}</span>
                    </div>
                  )}
                  {pdf.year && (
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-500">Year:</span>
                      <span className="text-gray-700">{pdf.year}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Extraction Type Selection */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-6 text-gray-900">Select Extraction Type</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {extractionTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => setSelectedType(type.id)}
                className={`relative overflow-hidden rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 ${selectedType === type.id
                    ? 'ring-4 ring-purple-500 ring-offset-2'
                    : ''
                  }`}
              >
                <div className={`bg-gradient-to-br ${type.color} p-6 text-white`}>
                  <div className="text-4xl mb-3">{type.icon}</div>
                  <h3 className="font-bold text-lg mb-2">{type.name}</h3>
                  <div className="text-sm opacity-90">
                    Click to select this extraction type
                  </div>
                </div>
                {selectedType === type.id && (
                  <div className="absolute top-3 right-3 bg-white rounded-full p-2">
                    <span className="text-purple-600 text-xl">✓</span>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Extraction Options */}
        {selectedType && (
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200 mb-8">
            <h2 className="text-2xl font-bold mb-6 text-gray-900">Extraction Configuration</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Page Range (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g., 1-50 or 10,20,30"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Output Format
                </label>
                <select className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all">
                  <option>JSON</option>
                  <option>Excel</option>
                  <option>CSV</option>
                  <option>PDF Report</option>
                </select>
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Additional Instructions (Optional)
              </label>
              <textarea
                placeholder="Enter any specific instructions for the extraction..."
                rows="4"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all resize-none"
              />
            </div>

            <button
              onClick={handleExtraction}
              disabled={extracting}
              className={`w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-4 rounded-xl text-lg font-semibold transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 ${extracting ? 'opacity-50 cursor-not-allowed' : ''
                }`}
            >
              {extracting ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Extracting...
                </span>
              ) : (
                '🚀 Start Extraction'
              )}
            </button>
          </div>
        )}

        {/* Results Section */}
        {extractedData && (
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Extraction Results</h2>
              <span className="bg-green-100 text-green-800 px-4 py-2 rounded-full font-semibold text-sm">
                ✓ {extractedData.status}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl">
                <div className="text-sm text-blue-600 font-medium mb-1">Extraction Type</div>
                <div className="text-lg font-bold text-blue-900">
                  {extractionTypes.find(t => t.id === extractedData.type)?.name}
                </div>
              </div>

              <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-xl">
                <div className="text-sm text-green-600 font-medium mb-1">Pages Covered</div>
                <div className="text-lg font-bold text-green-900">{extractedData.pagesCovered}</div>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-xl">
                <div className="text-sm text-purple-600 font-medium mb-1">Data Points</div>
                <div className="text-lg font-bold text-purple-900">{extractedData.dataPoints}</div>
              </div>

              <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-xl">
                <div className="text-sm text-orange-600 font-medium mb-1">Extracted At</div>
                <div className="text-lg font-bold text-orange-900">
                  {new Date(extractedData.extractedAt).toLocaleTimeString()}
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-6 rounded-xl mb-6">
              <h3 className="font-semibold text-gray-900 mb-2">Summary</h3>
              <p className="text-gray-700">{extractedData.summary}</p>
            </div>

            <div className="flex flex-wrap gap-4">
              <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-md">
                💾 Save Results
              </button>
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-md">
                📥 Download JSON
              </button>
              <button className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-md">
                📊 Export Report
              </button>
              <button className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-md">
                📧 Email Results
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-6">
            <ErrorMessage message={error} onRetry={handleExtraction} />
          </div>
        )}
      </div>
    </div>
  );
};

export default OtherExtraction;

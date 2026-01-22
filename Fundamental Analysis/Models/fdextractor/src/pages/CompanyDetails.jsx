import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { pdfService } from '../services/api';
import Loader from '../components/Loader';
import ErrorMessage from '../components/ErrorMessage';

const CompanyDetails = () => {
  const { pdfId } = useParams();
  const navigate = useNavigate();

  const [pdf, setPdf] = useState(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState(null);
  const [extractedData, setExtractedData] = useState(null);

  useEffect(() => {
    loadPDFInfo();
  }, [pdfId]);

  const loadPDFInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch PDF basic information
      const result = await pdfService.extractStatements(pdfId);
      setPdf(result.pdf);
    } catch (err) {
      setError(err.message || 'Failed to load PDF information');
    } finally {
      setLoading(false);
    }
  };

  const handleExtractCompanyDetails = async () => {
    try {
      setExtracting(true);
      setError(null);

      // This would call a new API endpoint for company details extraction
      // For now, we'll show a placeholder
      const result = {
        companyName: pdf.company || 'Unknown',
        registrationNumber: 'REG123456',
        address: '123 Business Street, City',
        phone: '+1 234 567 8900',
        email: 'info@company.com',
        website: 'www.company.com',
        industry: pdf.category || 'Financial Services',
        foundedYear: pdf.year || '2020',
        ceo: 'John Doe',
        employees: '1000+',
        description: 'Leading financial services provider...'
      };

      setExtractedData(result);
      alert('Company details extracted successfully!');
    } catch (err) {
      setError(err.message || 'Failed to extract company details');
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="container mx-auto px-6 py-8">
        {/* Back Button */}
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 mb-6 transition-colors group"
        >
          <span className="text-xl group-hover:-translate-x-1 transition-transform">←</span>
          <span className="font-medium">Back to Dashboard</span>
        </button>

        {/* Page Header */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 border border-gray-200">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
                  <span className="text-white text-2xl">🏢</span>
                </div>
                <div>
                  <h1 className="text-4xl font-bold text-gray-900">Company Details Extraction</h1>
                  <p className="text-gray-600 mt-1">Extract comprehensive company information</p>
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

        {/* Action Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
              <h2 className="text-2xl font-bold mb-4 text-gray-900">Extraction Options</h2>
              <p className="text-gray-600 mb-6">
                Select the type of company information you want to extract from this document.
              </p>

              <div className="space-y-4">
                <div className="flex items-center p-4 border-2 border-blue-200 rounded-xl bg-blue-50">
                  <input type="checkbox" id="basic" className="w-5 h-5 text-blue-600" defaultChecked />
                  <label htmlFor="basic" className="ml-3 flex-1">
                    <div className="font-semibold text-gray-900">Basic Information</div>
                    <div className="text-sm text-gray-600">Name, registration, contact details</div>
                  </label>
                </div>

                <div className="flex items-center p-4 border-2 border-blue-200 rounded-xl bg-blue-50">
                  <input type="checkbox" id="corporate" className="w-5 h-5 text-blue-600" defaultChecked />
                  <label htmlFor="corporate" className="ml-3 flex-1">
                    <div className="font-semibold text-gray-900">Corporate Structure</div>
                    <div className="text-sm text-gray-600">Board members, executives, ownership</div>
                  </label>
                </div>

                <div className="flex items-center p-4 border-2 border-gray-200 rounded-xl hover:border-blue-200 transition-colors">
                  <input type="checkbox" id="business" className="w-5 h-5 text-blue-600" />
                  <label htmlFor="business" className="ml-3 flex-1">
                    <div className="font-semibold text-gray-900">Business Overview</div>
                    <div className="text-sm text-gray-600">Industry, operations, subsidiaries</div>
                  </label>
                </div>
              </div>

              <button
                onClick={handleExtractCompanyDetails}
                disabled={extracting}
                className={`mt-6 w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-4 rounded-xl text-lg font-semibold transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 ${extracting ? 'opacity-50 cursor-not-allowed' : ''
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
          </div>

          <div className="lg:col-span-1">
            <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl shadow-lg p-8 text-white">
              <h3 className="text-xl font-bold mb-4">ℹ️ About This Feature</h3>
              <div className="space-y-3 text-sm">
                <p className="leading-relaxed">
                  This tool uses AI to extract company details from annual reports and financial documents.
                </p>
                <div className="bg-white/10 rounded-lg p-3 backdrop-blur-sm">
                  <p className="font-semibold mb-1">What you'll get:</p>
                  <ul className="space-y-1 text-xs">
                    <li>• Company registration info</li>
                    <li>• Contact information</li>
                    <li>• Leadership team</li>
                    <li>• Business structure</li>
                    <li>• Industry classification</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Results Section */}
        {extractedData && (
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <h2 className="text-2xl font-bold mb-6 text-gray-900">Extracted Company Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(extractedData).map(([key, value]) => (
                <div key={key} className="border-l-4 border-blue-500 pl-4 py-2">
                  <div className="text-sm text-gray-600 font-medium uppercase tracking-wide mb-1">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
                  </div>
                  <div className="text-gray-900 font-semibold">{value}</div>
                </div>
              ))}
            </div>

            <div className="mt-6 flex space-x-4">
              <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-md">
                💾 Save Results
              </button>
              <button className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-md">
                📥 Download JSON
              </button>
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-md">
                📊 Export Excel
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-6">
            <ErrorMessage message={error} onRetry={handleExtractCompanyDetails} />
          </div>
        )}
      </div>
    </div>
  );
};

export default CompanyDetails;

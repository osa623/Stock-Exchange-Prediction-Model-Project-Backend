import React, { useState, useEffect } from 'react';
import { pdfService } from '../services/api';
import PDFCard from '../components/PDFCard';
import Loader from '../components/Loader';
import ErrorMessage from '../components/ErrorMessage';

const Dashboard = () => {
  const [pdfsByCategory, setPdfsByCategory] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchPDFs();
  }, []);

  const fetchPDFs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await pdfService.getPDFsByCategory();
      setPdfsByCategory(data);
    } catch (err) {
      setError(err.message || 'Failed to load PDFs');
    } finally {
      setLoading(false);
    }
  };

  // Flatten all PDFs into a single array
  const allPDFs = React.useMemo(() => {
    return Object.keys(pdfsByCategory).flatMap((category) =>
      pdfsByCategory[category].map((pdf) => ({ ...pdf, category }))
    );
  }, [pdfsByCategory]);

  // Filter PDFs based on search term
  const filteredPDFs = React.useMemo(() => {
    if (!searchTerm) return allPDFs;

    return allPDFs.filter(
      (pdf) =>
        pdf.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pdf.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pdf.year?.toString().includes(searchTerm) ||
        pdf.category?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [allPDFs, searchTerm]);

  if (loading) {
    return <Loader message="Loading PDFs..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={fetchPDFs} />;
  }

  const totalPDFs = allPDFs.length;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-6 py-8">
        {/* Dashboard Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-semibold text-gray-900 mb-2">
            Financial Data Extractor
          </h1>
          <p className="text-gray-600 text-base">
            Manage and extract financial statements from PDFs with AI-powered analysis
          </p>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-gray-600 text-sm font-medium mb-1">Total PDFs</h3>
                <p className="text-3xl font-semibold text-gray-900">{totalPDFs}</p>
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <span className="text-gray-600 text-xl font-semibold">PDF</span>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-gray-600 text-sm font-medium mb-1">Categories</h3>
                <p className="text-3xl font-semibold text-gray-900">{Object.keys(pdfsByCategory).length}</p>
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <span className="text-gray-600 text-xl font-semibold">#</span>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-gray-600 text-sm font-medium mb-1">Status</h3>
                <p className="text-3xl font-semibold text-gray-900">Active</p>
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <span className="text-gray-600 text-xl font-semibold">✓</span>
              </div>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <div className="relative max-w-2xl">
            <input
              type="text"
              placeholder="Search by name, company, year, or category..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-5 py-3 pl-12 text-base rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition-all duration-200 shadow-sm"
            />
            <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 text-lg font-medium">
              ⌕
            </span>
          </div>
        </div>

        {/* PDFs Grid - 4 columns */}
        {filteredPDFs.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="text-4xl mb-4 text-gray-300 font-bold">No PDFs</div>
            <p className="text-gray-600 text-base mb-2">No PDFs found</p>
            <p className="text-gray-400 text-sm">Try adjusting your search criteria</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredPDFs.map((pdf) => (
              <PDFCard key={pdf.id} pdf={pdf} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;

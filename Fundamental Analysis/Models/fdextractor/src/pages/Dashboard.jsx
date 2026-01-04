import React, { useState, useEffect } from 'react';
import { pdfService } from '../services/api';
import CategorySection from '../components/CategorySection';
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

  const filteredCategories = React.useMemo(() => {
    if (!searchTerm) return pdfsByCategory;

    const filtered = {};
    Object.keys(pdfsByCategory).forEach((category) => {
      const filteredPDFs = pdfsByCategory[category].filter(
        (pdf) =>
          pdf.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          pdf.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          pdf.year?.toString().includes(searchTerm)
      );

      if (filteredPDFs.length > 0) {
        filtered[category] = filteredPDFs;
      }
    });

    return filtered;
  }, [pdfsByCategory, searchTerm]);

  if (loading) {
    return <Loader message="Loading PDFs..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={fetchPDFs} />;
  }

  const totalPDFs = Object.values(pdfsByCategory).reduce(
    (sum, pdfs) => sum + pdfs.length,
    0
  );

  return (
    <div className="container mx-auto px-6 py-8">
      {/* Dashboard Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Dashboard</h1>
        <p className="text-gray-600">
          Manage and extract financial statements from PDFs
        </p>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card p-6">
          <h3 className="text-gray-600 text-sm font-medium mb-1">Total PDFs</h3>
          <p className="text-3xl font-bold">{totalPDFs}</p>
        </div>
        <div className="card p-6">
          <h3 className="text-gray-600 text-sm font-medium mb-1">Categories</h3>
          <p className="text-3xl font-bold">{Object.keys(pdfsByCategory).length}</p>
        </div>
        <div className="card p-6">
          <h3 className="text-gray-600 text-sm font-medium mb-1">Status</h3>
          <p className="text-3xl font-bold">Active</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-8">
        <input
          type="text"
          placeholder="Search by name, company, or year..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input-field w-full md:w-96"
        />
      </div>

      {/* Categories */}
      {Object.keys(filteredCategories).length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600 text-lg">No PDFs found</p>
        </div>
      ) : (
        Object.keys(filteredCategories)
          .sort()
          .map((category) => (
            <CategorySection
              key={category}
              category={category}
              pdfs={filteredCategories[category]}
            />
          ))
      )}
    </div>
  );
};

export default Dashboard;

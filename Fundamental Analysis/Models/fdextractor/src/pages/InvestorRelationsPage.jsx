import { useParams, useNavigate } from 'react-router-dom';
import InvestorRelationsViewer from '../components/InvestorRelationsViewer';

const InvestorRelationsPage = () => {
  const { pdfId } = useParams();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="container mx-auto px-6 py-8">
        {/* Back Button */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 mb-6 transition-colors group"
        >
          <span className="text-xl group-hover:-translate-x-1 transition-transform">←</span>
          <span className="font-medium">Back to Dashboard</span>
        </button>

        {/* Page Header */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 border border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
              <span className="text-white text-2xl">📊</span>
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Investor Relations Extraction</h1>
              <p className="text-gray-600 mt-1">Extract investor relations data from PDF using OCR and TOC detection</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-6 text-sm bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center space-x-2">
              <span className="text-gray-500">📄 PDF ID:</span>
              <span className="font-semibold text-gray-900">{pdfId}</span>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <InvestorRelationsViewer pdfId={pdfId} />
      </div>
    </div>
  );
};

export default InvestorRelationsPage;

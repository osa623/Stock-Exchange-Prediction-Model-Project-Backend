import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import PDFDetail from './pages/PDFDetail';
import CompanyDetails from './pages/CompanyDetails';
import OtherExtraction from './pages/OtherExtraction';
import ShareholderPage from './pages/ShareholderPage';
import InvestorRelationsPage from './pages/InvestorRelationsPage';
import SubsidiaryPage from './pages/SubsidiaryPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-white">
        <Header />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          {/* Financial Statements Route - Original Flow */}
          <Route path="/pdf/:pdfId/statements" element={<PDFDetail />} />
          {/* Company Details Route - New Flow */}
          <Route path="/pdf/:pdfId/company" element={<CompanyDetails />} />
          {/* Other Extraction Route - New Flow */}
          <Route path="/pdf/:pdfId/other" element={<OtherExtraction />} />
          {/* Shareholder Extraction Route - New Flow */}
          <Route path="/pdf/:pdfId/shareholders" element={<ShareholderPage />} />
          {/* Investor Relations Route - New Flow */}
          <Route path="/pdf/:pdfId/investor-relations" element={<InvestorRelationsPage />} />
          {/* Subsidiary Route - New Flow */}
          <Route path="/pdf/:pdfId/subsidiary" element={<SubsidiaryPage />} />
          {/* Legacy Route - Redirect to statements */}
          <Route path="/pdf/:pdfId" element={<PDFDetail />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

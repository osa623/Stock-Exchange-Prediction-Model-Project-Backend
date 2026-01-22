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
import Home from './pages/Home';
import LoginPage from './pages/LoginPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-white">
        <Header />
        <Routes>
          <Route path="/home" element={<Home />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/pdf/:pdfId/statements" element={<PDFDetail />} />
          <Route path="/pdf/:pdfId/company" element={<CompanyDetails />} />
          <Route path="/pdf/:pdfId/other" element={<OtherExtraction />} />
          <Route path="/pdf/:pdfId/shareholders" element={<ShareholderPage />} />
          <Route path="/pdf/:pdfId/investor-relations" element={<InvestorRelationsPage />} />
          <Route path="/pdf/:pdfId/subsidiary" element={<SubsidiaryPage />} />
          <Route path="/pdf/:pdfId" element={<PDFDetail />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

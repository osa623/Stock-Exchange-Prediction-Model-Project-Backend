import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import PDFDetail from './pages/PDFDetail';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-white">
        <Header />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/pdf/:pdfId" element={<PDFDetail />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

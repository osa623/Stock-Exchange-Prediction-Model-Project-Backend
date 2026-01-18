import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div 
              className="flex items-center space-x-3 cursor-pointer group"
              onClick={() => navigate('/')}
            >
              <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center transform group-hover:scale-105 transition-transform duration-200">
                <span className="text-white text-lg font-bold">FD</span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  FD Extractor
                </h1>
                <span className="text-gray-500 text-xs">Financial Data Intelligence</span>
              </div>
            </div>
          </div>
          
          <nav className="flex items-center space-x-6">
            <button
              onClick={() => navigate('/')}
              className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                location.pathname === '/'
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              Dashboard
            </button>
            
            <div className="flex items-center space-x-3">
              <div className="text-right hidden md:block">
                <div className="text-sm font-medium text-gray-900">Admin User</div>
                <div className="text-xs text-gray-500">Administrator</div>
              </div>
              <div className="w-10 h-10 bg-gray-900 rounded-full flex items-center justify-center text-white font-semibold cursor-pointer hover:bg-gray-700 transition-colors duration-200">
                A
              </div>
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;

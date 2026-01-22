import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();


  const pathNames = {

    '/home': 'Home Section',
    '/dashboard': 'Annual PDF Extractor',
    '/login': 'Login Section',
  }


  const currentSection = pathNames[location.pathname] || 'Unknown Section';

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div
              className="flex items-center space-x-3 cursor-pointer group"
              onClick={() => navigate('/dashbaord')}
            >
              <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center transform group-hover:scale-105 transition-transform duration-200">
                <span className="text-white text-lg font-bold">BL</span>
              </div>
              <div>
                <h1 className="text-xl font-bold flex text-gray-900">
                  BUYZONLABS<div className='font-thin flex items-center px-2'>Panel ---
                    <h2 className='text-sm px-2 text-gray-500'>{currentSection}</h2>
                  </div>
                </h1>
                <span className="text-gray-500 text-xs">Admin Opeartions</span>
              </div>
            </div>
          </div>

          <nav className="flex items-center space-x-6">

            {location.pathname === '/login' ? (
              <button
                onClick={() => navigate('/home')}
                className={`hidden px-4 py-2 rounded-lg border-2 border-black font-medium transition-all duration-200 ${location.pathname === '/'
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
              >
                Back
              </button>
            ) : (
              <button
                onClick={() => navigate('/home')}
                className={`px-4 py-2 rounded-lg border-2 border-black font-medium transition-all duration-200 ${location.pathname === '/login'
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
              >
                Back
              </button>
            )}


            {location.pathname === '/login' ? null
              : (
                <div className="flex items-center space-x-3">
                  <div className="text-right hidden md:block">
                    <div className="text-sm font-medium text-gray-900">Admin User</div>
                    <div className="text-xs text-gray-500">Administrator</div>
                  </div>
                  <div className="w-10 h-10 bg-gray-900 rounded-full flex items-center justify-center text-white font-semibold cursor-pointer hover:bg-gray-700 transition-colors duration-200">
                    A
                  </div>
                </div>
              )}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;

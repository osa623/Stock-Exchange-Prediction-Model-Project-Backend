import React from 'react';

const Header = () => {
  return (
    <header className="bg-black text-white shadow-md">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold">FD Extractor</h1>
            <span className="text-gray-300 text-sm">Admin Panel</span>
          </div>
          <nav className="flex items-center space-x-6">
            <a href="/" className="hover:text-gray-300 transition-colors">
              Dashboard
            </a>
            <div className="h-8 w-8 bg-white rounded-full flex items-center justify-center text-black font-semibold">
              A
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;

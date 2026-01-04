import React from 'react';

const ErrorMessage = ({ message, onRetry }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <div className="bg-white border-2 border-black rounded-lg p-8 max-w-md text-center">
        <div className="text-4xl mb-4">⚠️</div>
        <h3 className="text-xl font-semibold mb-2">Error</h3>
        <p className="text-gray-600 mb-6">{message || 'An unexpected error occurred'}</p>
        {onRetry && (
          <button onClick={onRetry} className="btn-primary">
            Try Again
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorMessage;

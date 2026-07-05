import React from 'react';

const LoadingScreen = () => {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-50">
      <div className="flex flex-col items-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
        <p className="mt-4 text-slate-500 font-medium">Loading...</p>
      </div>
    </div>
  );
};

export default LoadingScreen;

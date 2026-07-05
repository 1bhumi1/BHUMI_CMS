import React, { useEffect } from 'react';
import { Navigate, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/AuthContext';
import LoadingScreen from './LoadingScreen';

const RoleRouter = () => {
  const { dashboard, isLoading, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      if (dashboard) {
        // Automatically route to the correct dashboard if we land on /dashboard
        if (window.location.pathname === '/dashboard' || window.location.pathname === '/dashboard/') {
          navigate(dashboard, { replace: true });
        }
      }
    }
  }, [isLoading, isAuthenticated, dashboard, navigate]);

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // If this is just a wrapper for routing, render children routes
  return <Outlet />;
};

export default RoleRouter;

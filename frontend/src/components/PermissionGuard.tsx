import React, { ReactNode } from 'react';
import { useAuth } from '../lib/AuthContext';

interface PermissionGuardProps {
  permission: string;
  children: ReactNode;
  fallback?: ReactNode;
}

const PermissionGuard = ({ permission, children, fallback = null }: PermissionGuardProps) => {
  const { hasPermission } = useAuth();

  if (!hasPermission(permission)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

export default PermissionGuard;

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getAccessToken, setTokens, removeTokens } from './auth';
import { api } from './api';
import { jwtDecode } from 'jwt-decode';

export interface User {
  id: number;
  name: string;
  computer_code: number;
  role: string;
  department: string | null;
}

export interface AuthContextType {
  user: User | null;
  role: string | null;
  department: string | null;
  permissions: string[];
  dashboard: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isImpersonating: boolean;
  originalUser: string | null;
  login: (data: any) => void;
  logout: () => void;
  hasRole: (roles: string[]) => boolean;
  hasPermission: (permission: string) => boolean;
  isAdmin: () => boolean;
  isStaff: () => boolean;
  isStudent: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [department, setDepartment] = useState<string | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [dashboard, setDashboard] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isImpersonating, setIsImpersonating] = useState<boolean>(false);
  const [originalUser, setOriginalUser] = useState<string | null>(null);

  // Rehydrate state on load
  useEffect(() => {
    const hydrate = () => {
      const storedUser = localStorage.getItem('user');
      const storedRole = localStorage.getItem('role');
      const storedPermissions = localStorage.getItem('permissions');
      const storedDashboard = localStorage.getItem('dashboard');
      const token = getAccessToken();

      if (token && storedUser) {
        const parsedUser = JSON.parse(storedUser);
        
        setUser(parsedUser);
        setRole(storedRole);
        setDepartment(parsedUser?.department || null);
        setPermissions(storedPermissions ? JSON.parse(storedPermissions) : []);
        setDashboard(storedDashboard);
        setIsAuthenticated(true);
        
        try {
          const decoded: any = jwtDecode(token);
          if (decoded.impersonating) {
            setIsImpersonating(true);
            setOriginalUser(decoded.actor_role?.toLowerCase() === 'admin' ? 'Administrator' : decoded.actor_role);
          } else {
            setIsImpersonating(false);
            setOriginalUser(null);
          }
        } catch (e) {
          setIsImpersonating(false);
          setOriginalUser(null);
        }
      } else {
        setIsAuthenticated(false);
        setIsImpersonating(false);
        setOriginalUser(null);
      }
      setIsLoading(false);
    };
    hydrate();
  }, []);

  const login = (data: any) => {
    // Save to local storage
    setTokens(data.access_token, data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    localStorage.setItem('role', data.user.role);
    localStorage.setItem('permissions', JSON.stringify(data.permissions));
    localStorage.setItem('dashboard', data.dashboard);

    // Update state
    setUser(data.user);
    setRole(data.user.role);
    setDepartment(data.user.department || null);
    setPermissions(data.permissions);
    setDashboard(data.dashboard);
    setIsAuthenticated(true);
    
    if (data.access_token) {
      try {
        const decoded: any = jwtDecode(data.access_token);
        if (decoded.impersonating) {
          setIsImpersonating(true);
          setOriginalUser(decoded.actor_role?.toLowerCase() === 'admin' ? 'Administrator' : decoded.actor_role);
        } else {
          setIsImpersonating(false);
          setOriginalUser(null);
        }
      } catch (e) {
        setIsImpersonating(false);
        setOriginalUser(null);
      }
    }
  };

  const logout = () => {
    removeTokens();
    localStorage.removeItem('user');
    localStorage.removeItem('role');
    localStorage.removeItem('permissions');
    localStorage.removeItem('dashboard');
    setUser(null);
    setRole(null);
    setDepartment(null);
    setPermissions([]);
    setDashboard(null);
    setIsAuthenticated(false);
    setIsImpersonating(false);
    setOriginalUser(null);
  };

  const hasRole = (allowedRoles: string[]) => {
    if (!role) return false;
    return allowedRoles.includes(role);
  };

  const hasPermission = (permission: string) => {
    return permissions.includes(permission);
  };

  const isAdmin = () => {
    return dashboard === '/dashboard/admin';
  };

  const isStaff = () => {
    return dashboard === '/dashboard/staff';
  };

  const isStudent = () => {
    return dashboard === '/dashboard/student';
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        department,
        permissions,
        dashboard,
        isAuthenticated,
        isLoading,
        isImpersonating,
        originalUser,
        login,
        logout,
        hasRole,
        hasPermission,
        isAdmin,
        isStaff,
        isStudent
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

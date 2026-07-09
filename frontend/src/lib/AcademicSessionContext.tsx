import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface AcademicSessionContextType {
  currentSession: string;
  setSession: (session: string) => void;
}

const AcademicSessionContext = createContext<AcademicSessionContextType | undefined>(undefined);

export const AcademicSessionProvider = ({ children }: { children: ReactNode }) => {
  const [currentSession, setCurrentSessionState] = useState<string>(() => {
    return localStorage.getItem('academic_session') || '2025-2026 (July-Dec)';
  });

  const setSession = (session: string) => {
    setCurrentSessionState(session);
    localStorage.setItem('academic_session', session);
  };

  return (
    <AcademicSessionContext.Provider value={{ currentSession, setSession }}>
      {children}
    </AcademicSessionContext.Provider>
  );
};

export const useAcademicSession = () => {
  const context = useContext(AcademicSessionContext);
  if (context === undefined) {
    throw new Error('useAcademicSession must be used within an AcademicSessionProvider');
  }
  return context;
};

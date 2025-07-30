import { createContext, useContext, useState, ReactNode, useEffect } from 'react';

// Definisce l'interfaccia per il contesto di autenticazione
interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
}

// Crea il contesto con un valore di default
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Props del provider
interface AuthProviderProps {
  children: ReactNode;
}

// Provider che gestisce lo stato di autenticazione
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const initialToken = localStorage.getItem('authToken');
  console.log('[AUTH_DEBUG] AuthProvider initialized with token:', { 
    hasToken: !!initialToken, 
    tokenLength: initialToken?.length,
    tokenPreview: initialToken?.substring(0, 20) + '...' 
  });
  
  const [token, setToken] = useState<string | null>(initialToken);

  const login = (newToken: string) => {
    console.log('[AUTH_DEBUG] login() called with token:', { 
      hasToken: !!newToken, 
      tokenLength: newToken?.length,
      tokenPreview: newToken?.substring(0, 20) + '...' 
    });
    
    setToken(newToken);
    localStorage.setItem('authToken', newToken);
    
    console.log('[AUTH_DEBUG] Token saved to localStorage');
    
    // Verify storage immediately
    const stored = localStorage.getItem('authToken');
    console.log('[AUTH_DEBUG] Verification after storage:', { 
      storedSuccessfully: stored === newToken,
      storedLength: stored?.length 
    });
  };

  const logout = () => {
    console.log('[AUTH_DEBUG] logout() called');
    setToken(null);
    localStorage.removeItem('authToken');
    console.log('[AUTH_DEBUG] Token removed from localStorage');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated: !!token, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook per accedere al contesto
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
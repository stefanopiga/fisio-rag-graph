import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AuthProvider, useAuth } from './hooks/useAuth';
import LoginPage from './components/LoginPage';

// Wrapper per gestire la logica di autenticazione
const AppWrapper = () => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <App /> : <LoginPage />;
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <AppWrapper />
    </AuthProvider>
  </React.StrictMode>
);
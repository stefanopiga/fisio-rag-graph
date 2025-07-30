import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { config } from '../config';
import styled from 'styled-components';

const LoginContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #1f2937;
`;

const LoginForm = styled.form`
  padding: 40px;
  background-color: #374151;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 350px;
`;

const Input = styled.input`
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #4b5563;
  background-color: #1f2937;
  color: #d1d5db;
  font-size: 16px;
`;

const Button = styled.button`
  padding: 10px;
  border-radius: 4px;
  border: none;
  background-color: #3b82f6;
  color: white;
  font-size: 16px;
  cursor: pointer;

  &:hover {
    background-color: #2563eb;
  }
`;

const Title = styled.h2`
  color: #d1d5db;
  text-align: center;
`;

const ErrorMessage = styled.p`
  color: #f87171;
  text-align: center;
`;

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    console.log('[LOGIN_DEBUG] Starting login process', { username, passwordLength: password.length });
    console.log('[LOGIN_DEBUG] API URL:', config.apiUrl);

    try {
      const loginUrl = `${config.apiUrl}/auth/login`;
      console.log('[LOGIN_DEBUG] Making request to:', loginUrl);
      
      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      console.log('[LOGIN_DEBUG] Response status:', response.status, response.statusText);
      console.log('[LOGIN_DEBUG] Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[LOGIN_DEBUG] Login failed:', response.status, errorText);
        throw new Error(`Login failed: ${response.status} - ${errorText || 'Credenziali non valide'}`);
      }

      const data = await response.json();
      
      // ULTRA-DEBUG: Log the exact response structure
      console.log('[LOGIN_DEBUG] RAW Response Data:', JSON.stringify(data, null, 2));
      console.log('[LOGIN_DEBUG] data.token:', data.token);
      console.log('[LOGIN_DEBUG] data.token?.access_token:', data.token?.access_token);
      
      console.log('[LOGIN_DEBUG] Login response received:', { 
        hasAccessToken: !!data.token?.access_token, 
        tokenLength: data.token?.access_token?.length,
        expires_in: data.token?.expires_in,
        token_type: data.token?.token_type,
        hasUser: !!data.user,
        session_id: data.session_id
      });

      if (!data.token?.access_token) {
        console.error('[LOGIN_DEBUG] DETAILED ERROR - No access_token in token object!');
        console.error('[LOGIN_DEBUG] Full data object:', data);
        console.error('[LOGIN_DEBUG] data.token type:', typeof data.token);
        console.error('[LOGIN_DEBUG] data.token keys:', data.token ? Object.keys(data.token) : 'token is null/undefined');
        throw new Error('CRITICAL ERROR: No access token received in response');
      }

      console.log('[LOGIN_DEBUG] Calling login() with token');
      login(data.token.access_token);
      
      // Verify token was saved
      setTimeout(() => {
        const savedToken = localStorage.getItem('authToken');
        console.log('[LOGIN_DEBUG] Token verification after login:', { 
          tokenSaved: !!savedToken, 
          tokenMatches: savedToken === data.access_token,
          savedTokenLength: savedToken?.length 
        });
      }, 100);

    } catch (err: any) {
      console.error('[LOGIN_DEBUG] Login error:', err);
      setError(err.message || 'Errore durante il login');
    }
  };

  return (
    <LoginContainer>
      <LoginForm onSubmit={handleSubmit}>
        <Title>Accesso a Fisio RAG v2.0-DEBUG</Title>
        <Input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <Button type="submit">Login</Button>
        {error && <ErrorMessage>{error}</ErrorMessage>}
      </LoginForm>
    </LoginContainer>
  );
};

export default LoginPage;
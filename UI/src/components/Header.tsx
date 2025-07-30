import React from 'react';
import styled from 'styled-components';

// Using simple text icons instead of Ant Design for now
const HeaderContainer = styled.div`
  grid-column: 1 / -1;
  background-color: #1f2937;
  color: #d1d5db;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #374151;
  height: 60px;
`;

const Title = styled.h1`
  font-size: 20px;
  font-weight: 600;
`;

const StatusContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
`;

const LogoutButton = styled.button`
  background: none;
  border: none;
  color: #d1d5db;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;

  &:hover {
    color: #ef4444;
  }
`;

interface HeaderProps {
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'error';
  onReconnect: () => void;
  onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({ connectionStatus, onReconnect, onLogout }) => {
  const getStatus = () => {
    switch (connectionStatus) {
      case 'connected':
        return { icon: '🟢', text: 'Connesso' };
      case 'connecting':
        return { icon: '🔄', text: 'In connessione...' };
      case 'disconnected':
        return { icon: '🟡', text: 'Disconnesso' };
      case 'error':
        return { icon: '🔴', text: 'Errore' };
    }
  };

  const { icon, text } = getStatus();

  return (
    <HeaderContainer>
      <Title>Fisio RAG+Graph</Title>
      <StatusContainer>
        <StatusIndicator onClick={onReconnect}>
          <span>{icon}</span>
          <span>{text}</span>
        </StatusIndicator>
        <LogoutButton onClick={onLogout}>
          <span>⏻</span>
          <span>Logout</span>
        </LogoutButton>
      </StatusContainer>
    </HeaderContainer>
  );
};

export default Header;
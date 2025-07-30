import React from 'react';
import styled from 'styled-components';
import { tokens } from '../styles/design-tokens';
import Header from './Header';
import Sidebar from './Sidebar';
import MainContent from './MainContent';
import RightSidebar from './RightSidebar';

const AppContainer = styled.div`
  display: grid;
  grid-template-columns: 18rem 1fr 20rem;
  grid-template-rows: auto 1fr;
  height: 100vh;
  gap: 1px;
  background-color: ${tokens.semantic.border.primary};
`;

interface LayoutProps {
  children?: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <AppContainer>
      <Header />
      <Sidebar />
      <MainContent />
      <RightSidebar />
    </AppContainer>
  );
};

export default Layout;
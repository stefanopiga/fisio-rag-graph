import styled, { createGlobalStyle } from 'styled-components';
import { tokens } from './design-tokens';

export const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: ${tokens.typography.fontFamily.primary};
    background-color: ${tokens.semantic.background.primary};
    color: ${tokens.semantic.text.primary};
    height: 100vh;
    overflow: hidden;
    font-size: ${tokens.typography.fontSize.base};
    line-height: ${tokens.typography.lineHeight.normal};
  }

  #root {
    height: 100vh;
  }

  /* Scrollbar styling */
  ::-webkit-scrollbar {
    width: 6px;
  }

  ::-webkit-scrollbar-track {
    background: ${tokens.semantic.background.secondary};
  }

  ::-webkit-scrollbar-thumb {
    background: ${tokens.semantic.border.primary};
    border-radius: ${tokens.borderRadius.base};
  }

  ::-webkit-scrollbar-thumb:hover {
    background: ${tokens.semantic.border.secondary};
  }
`;
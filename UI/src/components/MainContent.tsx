import React from 'react';
import styled from 'styled-components';
import { tokens } from '../styles/design-tokens';
import { Message, ChatMode } from '../types';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';

const MainContainer = styled.main`
  background-color: ${tokens.semantic.background.tertiary};
  display: flex;
  flex-direction: column;
  height: 100vh; // Occupies the full viewport height
`;

const ChatHeader = styled.div`
  padding: ${tokens.spacing[4]} ${tokens.spacing[6]};
  border-bottom: 1px solid ${tokens.semantic.border.primary};
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0; // Prevents the header from shrinking
`;

const CurrentChatTitle = styled.div`
  font-size: ${tokens.typography.fontSize.lg};
  font-weight: ${tokens.typography.fontWeight.semibold};
  color: ${tokens.semantic.text.primary};
`;

const ModelIndicator = styled.div`
  font-size: ${tokens.typography.fontSize.xs};
  color: ${tokens.semantic.text.tertiary};
  background-color: rgba(55, 65, 81, 0.8);
  padding: ${tokens.spacing[2]} ${tokens.spacing[3]};
  border-radius: ${tokens.borderRadius.md};
  border: 1px solid ${tokens.semantic.border.secondary};
`;

const MessagesContainer = styled.div`
  flex: 1; // Allows this container to grow and fill available space
  overflow-y: auto; // Enables scrolling for message content
  padding: ${tokens.spacing[6]};
`;

const InputContainer = styled.div`
  flex-shrink: 0; // Prevents the input area from shrinking
  padding: ${tokens.spacing[4]};
  border-top: 1px solid ${tokens.semantic.border.primary};
`;

interface MainContentProps {
  messages: Message[];
  chatTitle: string;
  currentModel: string;
  onSendMessage: (content: string, mode: ChatMode) => void;
  isLoading?: boolean;
}

const MainContent: React.FC<MainContentProps> = ({
  messages,
  chatTitle,
  currentModel,
  onSendMessage,
  isLoading = false
}) => {
  return (
    <MainContainer>
      <ChatHeader>
        <CurrentChatTitle>{chatTitle}</CurrentChatTitle>
        <ModelIndicator>{currentModel}</ModelIndicator>
      </ChatHeader>
      
      <MessagesContainer>
        <ChatMessages messages={messages} isLoading={isLoading} />
      </MessagesContainer>
      
      <InputContainer>
        <ChatInput onSendMessage={onSendMessage} disabled={isLoading} />
      </InputContainer>
    </MainContainer>
  );
};

export default MainContent;
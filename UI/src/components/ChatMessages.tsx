import React, { useEffect, useRef } from 'react';
import styled from 'styled-components';
import { tokens } from '../styles/design-tokens';
import { Message } from '../types';

const MessagesArea = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${tokens.spacing[5]};
`;

const MessageContainer = styled.div<{ $isUser: boolean }>`
  display: flex;
  gap: ${tokens.spacing[4]};
  max-width: 80%;
  ${props => props.$isUser && `
    align-self: flex-end;
    flex-direction: row-reverse;
  `}
`;

const MessageAvatar = styled.div<{ $isUser: boolean }>`
  width: 2rem;
  height: 2rem;
  border-radius: ${tokens.borderRadius.full};
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: ${tokens.typography.fontSize.xs};
  font-weight: ${tokens.typography.fontWeight.medium};
  
  ${props => props.$isUser ? `
    background: linear-gradient(135deg, #10b981, #059669);
  ` : `
    background: linear-gradient(135deg, ${tokens.semantic.accent.primary}, ${tokens.semantic.accent.hover});
  `}
`;

const MessageBubble = styled.div<{ $isUser: boolean }>`
  background-color: ${props => props.$isUser 
    ? 'rgba(59, 130, 246, 0.15)' 
    : 'rgba(55, 65, 81, 0.8)'};
  border-radius: ${tokens.borderRadius['2xl']};
  padding: ${tokens.spacing[4]} ${tokens.spacing[5]};
  border: 1px solid ${props => props.$isUser 
    ? tokens.semantic.accent.primary 
    : tokens.semantic.border.secondary};
  backdrop-filter: blur(8px);
  position: relative;
  line-height: ${tokens.typography.lineHeight.relaxed};
`;

const MessageTime = styled.div`
  font-size: ${tokens.typography.fontSize.xs};
  color: ${tokens.semantic.text.tertiary};
  margin-top: ${tokens.spacing[2]};
`;

const LoadingIndicator = styled.div`
  display: flex;
  gap: 4px;
  padding: ${tokens.spacing[2]};
  
  span {
    width: 6px;
    height: 6px;
    background-color: ${tokens.semantic.text.tertiary};
    border-radius: ${tokens.borderRadius.full};
    animation: bounce 1.4s infinite ease-in-out both;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
  
  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }
`;

interface ChatMessagesProps {
  messages: Message[];
  isLoading?: boolean;
}

const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, isLoading }) => {
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('it-IT', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <MessagesArea>
      {messages.map((message) => (
        <MessageContainer key={message.id} $isUser={message.role === 'user'}>
          <MessageAvatar $isUser={message.role === 'user'}>
            {message.role === 'user' ? 'TU' : 'AI'}
          </MessageAvatar>
          <MessageBubble $isUser={message.role === 'user'}>
            <div>{message.content}</div>
            <MessageTime>{formatTime(message.timestamp)}</MessageTime>
          </MessageBubble>
        </MessageContainer>
      ))}
      
      {isLoading && (
        <MessageContainer $isUser={false}>
          <MessageAvatar $isUser={false}>AI</MessageAvatar>
          <MessageBubble $isUser={false}>
            <LoadingIndicator>
              <span></span>
              <span></span>
              <span></span>
            </LoadingIndicator>
          </MessageBubble>
        </MessageContainer>
      )}
      <div ref={endOfMessagesRef} />
    </MessagesArea>
  );
};

export default ChatMessages;
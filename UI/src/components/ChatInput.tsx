import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { tokens } from '../styles/design-tokens';
import { ChatMode } from '../types';

const InputArea = styled.div`
  padding: ${tokens.spacing[6]};
  border-top: 1px solid ${tokens.semantic.border.primary};
`;

const InputWrapper = styled.div`
  background-color: rgba(55, 65, 81, 0.8);
  border-radius: ${tokens.borderRadius['2xl']};
  border: 1px solid ${tokens.semantic.border.secondary};
  overflow: hidden;
  transition: border-color 0.15s ease;

  &:focus-within {
    border-color: ${tokens.semantic.accent.primary};
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

const InputControls = styled.div`
  display: flex;
  align-items: center;
  padding: ${tokens.spacing[3]} ${tokens.spacing[4]};
  border-bottom: 1px solid ${tokens.semantic.border.secondary};
  gap: ${tokens.spacing[3]};
`;

const ModeSelector = styled.select`
  background: transparent;
  color: ${tokens.semantic.text.secondary};
  border: none;
  font-size: ${tokens.typography.fontSize.sm};
  cursor: pointer;
  padding: ${tokens.spacing[1]} ${tokens.spacing[2]};
  border-radius: ${tokens.borderRadius.md};
  
  &:hover {
    background-color: rgba(55, 65, 81, 0.8);
  }

  option {
    background-color: ${tokens.semantic.background.secondary};
    color: ${tokens.semantic.text.primary};
  }
`;

const InputField = styled.div`
  display: flex;
  align-items: flex-end;
`;

const MessageInput = styled.textarea`
  flex: 1;
  background: transparent;
  color: ${tokens.semantic.text.primary};
  padding: ${tokens.spacing[4]} ${tokens.spacing[5]};
  font-size: ${tokens.typography.fontSize.base};
  border: none;
  outline: none;
  resize: none;
  min-height: 1.5rem;
  max-height: 8rem;
  font-family: ${tokens.typography.fontFamily.primary};

  &::placeholder {
    color: ${tokens.semantic.text.tertiary};
  }
`;

const SendControls = styled.div`
  display: flex;
  align-items: flex-end;
  padding: ${tokens.spacing[4]};
  gap: ${tokens.spacing[2]};
`;

const ActionButton = styled.button`
  padding: ${tokens.spacing[2]};
  border-radius: ${tokens.borderRadius.md};
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
  background: transparent;
  color: ${tokens.semantic.text.tertiary};
  font-size: ${tokens.typography.fontSize.base};

  &:hover {
    background-color: rgba(55, 65, 81, 0.8);
    color: ${tokens.semantic.text.secondary};
  }
`;

const SendButton = styled.button`
  background: linear-gradient(135deg, ${tokens.semantic.accent.primary}, ${tokens.semantic.accent.hover});
  color: ${tokens.semantic.text.primary};
  padding: ${tokens.spacing[3]} ${tokens.spacing[4]};
  font-weight: ${tokens.typography.fontWeight.medium};
  border: none;
  border-radius: ${tokens.borderRadius.md};
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: linear-gradient(135deg, ${tokens.semantic.accent.secondary}, ${tokens.semantic.accent.hover});
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const modeOptions: { value: ChatMode; label: string; icon: string }[] = [
  { value: 'normal', label: 'Chat Normale', icon: '💬' },
  { value: 'study', label: 'Modalità Studio', icon: '📝' },
  { value: 'problem-solving', label: 'Risoluzione Problemi', icon: '🧪' },
  { value: 'data-analysis', label: 'Analisi Dati', icon: '📊' }
];

interface ChatInputProps {
  onSendMessage: (content: string, mode: ChatMode) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled = false }) => {
  const [message, setMessage] = useState('');
  const [mode, setMode] = useState<ChatMode>('normal');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 128) + 'px';
    }
  }, [message]);

  const handleSubmit = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim(), mode);
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <InputArea>
      <InputWrapper>
        <InputControls>
          <ModeSelector 
            value={mode} 
            onChange={(e) => setMode(e.target.value as ChatMode)}
          >
            {modeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.icon} {option.label}
              </option>
            ))}
          </ModeSelector>
        </InputControls>
        
        <InputField>
          <MessageInput
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Scrivi la tua domanda o comando..."
            disabled={disabled}
            rows={1}
          />
          <SendControls>
            <ActionButton>📎</ActionButton>
            <ActionButton>🎤</ActionButton>
            <ActionButton>📷</ActionButton>
            <SendButton onClick={handleSubmit} disabled={disabled || !message.trim()}>
              Invia
            </SendButton>
          </SendControls>
        </InputField>
      </InputWrapper>
    </InputArea>
  );
};

export default ChatInput;
import React from 'react';
import styled from 'styled-components';
import { tokens } from '../styles/design-tokens';
import { Chat } from '../types';

const SidebarContainer = styled.aside`
  background-color: ${tokens.semantic.background.secondary};
  padding: ${tokens.spacing[4]};
  overflow-y: auto;
  display: flex;
  flex-direction: column;
`;

const NewChatButton = styled.button`
  width: 100%;
  background: linear-gradient(135deg, ${tokens.semantic.accent.primary}, ${tokens.semantic.accent.hover});
  color: ${tokens.semantic.text.primary};
  padding: ${tokens.spacing[3]} ${tokens.spacing[4]};
  border-radius: ${tokens.borderRadius.lg};
  font-size: ${tokens.typography.fontSize.sm};
  font-weight: ${tokens.typography.fontWeight.medium};
  border: none;
  cursor: pointer;
  margin-bottom: ${tokens.spacing[6]};
  transition: all 0.15s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }
`;

const Section = styled.div`
  margin-bottom: ${tokens.spacing[8]};
`;

const SectionTitle = styled.div`
  font-size: ${tokens.typography.fontSize.xs};
  font-weight: ${tokens.typography.fontWeight.semibold};
  color: ${tokens.semantic.text.tertiary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: ${tokens.spacing[3]};
`;

const ChatList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${tokens.spacing[2]};
`;

interface ChatItemProps {
  $isActive?: boolean;
}

const ChatItem = styled.div<ChatItemProps>`
  padding: ${tokens.spacing[3]};
  border-radius: ${tokens.borderRadius.lg};
  font-size: ${tokens.typography.fontSize.sm};
  color: ${tokens.semantic.text.secondary};
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid transparent;
  position: relative;

  &:hover {
    background-color: ${tokens.semantic.border.primary};
    border-color: ${tokens.semantic.border.secondary};
  }

  ${props => props.$isActive && `
    background-color: rgba(59, 130, 246, 0.2);
    border-color: ${tokens.semantic.accent.primary};
    color: ${tokens.semantic.text.primary};
  `}
`;

const ChatPreview = styled.div`
  font-size: ${tokens.typography.fontSize.xs};
  color: ${tokens.semantic.text.tertiary};
  margin-top: ${tokens.spacing[1]};
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

interface SidebarProps {
  chats: Chat[];
  activeChat?: string;
  onChatSelect: (chatId: string) => void;
  onNewChat: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  chats, 
  activeChat, 
  onChatSelect, 
  onNewChat 
}) => {
  const sortedChats = [...chats].sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
  
  const studySubjects = [
    { id: 'anatomia', title: 'Anatomia', icon: '📚' },
    { id: 'fisiologia', title: 'Fisiologia', icon: '🦴' },
    { id: 'patologia', title: 'Patologia', icon: '⚕️' },
    { id: 'kinesiologia', title: 'Kinesiologia', icon: '🏃‍♂️' },
    { id: 'biomeccanica', title: 'Biomeccanica', icon: '🔬' },
  ];

  const userProfile = {
    name: 'Mario Rossi',
    avatar: 'TU'
  };
  
  return (
    <SidebarContainer>
      <NewChatButton onClick={onNewChat}>
        + Nuova Conversazione
      </NewChatButton>
      
      <Section>
        <SectionTitle>Conversazioni Recenti</SectionTitle>
        <ChatList>
          {sortedChats.map((chat) => (
            <ChatItem
              key={chat.id}
              $isActive={chat.id === activeChat}
              onClick={() => onChatSelect(chat.id)}
            >
              <div>{chat.title}</div>
              <ChatPreview>{chat.preview || 'Nessuna anteprima'}</ChatPreview>
            </ChatItem>
          ))}
        </ChatList>
      </Section>

      <Section>
        <SectionTitle>Materie di Studio</SectionTitle>
        <ChatList>
          {studySubjects.map(subject => (
            <ChatItem key={subject.id}>
              {subject.icon} {subject.title}
            </ChatItem>
          ))}
        </ChatList>
      </Section>
      
      {/* User Profile Section */}
      <Section style={{ marginTop: 'auto' }}>
        <SectionTitle>Profilo</SectionTitle>
        <ChatItem>
          <div style={{ display: 'flex', alignItems: 'center', gap: tokens.spacing[3] }}>
            <div style={{ 
              width: '2rem', height: '2rem', borderRadius: '50%', 
              background: 'linear-gradient(135deg, #10b981, #059669)', 
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 'bold'
            }}>
              {userProfile.avatar}
            </div>
            <span>{userProfile.name}</span>
          </div>
        </ChatItem>
      </Section>
    </SidebarContainer>
  );
};

export default Sidebar;
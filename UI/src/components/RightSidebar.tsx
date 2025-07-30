import React from 'react';
import styled from 'styled-components';
import { tokens } from '../styles/design-tokens';
import { Tool, ContextItem } from '../types';

const SidebarContainer = styled.aside`
  background-color: ${tokens.semantic.background.secondary};
  padding: ${tokens.spacing[4]};
  overflow-y: auto;
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

const ToolsPanel = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${tokens.spacing[2]};
`;

const ToolItem = styled.div`
  display: flex;
  align-items: center;
  gap: ${tokens.spacing[3]};
  padding: ${tokens.spacing[3]};
  border-radius: ${tokens.borderRadius.lg};
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background-color: ${tokens.semantic.border.primary};
  }
`;

const ToolIcon = styled.div`
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: ${tokens.typography.fontSize.sm};
`;

const ToolInfo = styled.div`
  flex: 1;
`;

const ToolName = styled.div`
  font-size: ${tokens.typography.fontSize.sm};
  font-weight: ${tokens.typography.fontWeight.medium};
  color: ${tokens.semantic.text.primary};
`;

const ToolDescription = styled.div`
  font-size: ${tokens.typography.fontSize.xs};
  color: ${tokens.semantic.text.tertiary};
`;

const ContextPanel = styled.div`
  background-color: ${tokens.semantic.surface.primary};
  border-radius: ${tokens.borderRadius.xl};
  border: 1px solid ${tokens.semantic.border.primary};
  padding: ${tokens.spacing[4]};
`;

const ContextItemContainer = styled.div`
  padding: ${tokens.spacing[3]};
  border-radius: ${tokens.borderRadius.lg};
  background-color: ${tokens.semantic.surface.secondary};
  border: 1px solid ${tokens.semantic.border.secondary};
  margin-bottom: ${tokens.spacing[3]};
`;

const ContextTitle = styled.div`
  font-size: ${tokens.typography.fontSize.sm};
  font-weight: ${tokens.typography.fontWeight.medium};
  color: ${tokens.semantic.text.primary};
  margin-bottom: ${tokens.spacing[1]};
`;

const ContextPreview = styled.div`
  font-size: ${tokens.typography.fontSize.xs};
  color: ${tokens.semantic.text.tertiary};
  line-height: ${tokens.typography.lineHeight.normal};
`;

const ContextItemWrapper = styled.div`
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
`;

const defaultTools: Tool[] = [
  {
    id: 'pdf-analyzer',
    name: 'Analizzatore PDF',
    description: 'Estrae testo da documenti',
    icon: '📊',
    isActive: true
  },
  {
    id: 'calculator',
    name: 'Calcolatrice',
    description: 'Risolve equazioni',
    icon: '🧮',
    isActive: true
  },
  {
    id: 'anatomy-db',
    name: 'Database Anatomico',
    description: 'Ricerca strutture anatomiche',
    icon: '📚',
    isActive: true
  },
  {
    id: 'quiz-generator',
    name: 'Quiz Generator',
    description: 'Crea test personalizzati',
    icon: '🎯',
    isActive: true
  }
];

const defaultContext: ContextItem[] = [
  {
    id: 'grays-anatomy',
    title: "📖 Libro: Gray's Anatomy",
    preview: 'Capitolo 3: Sistema Nervoso Centrale - Organizzazione funzionale...',
    type: 'document'
  },
  {
    id: 'lesson-15',
    title: '📝 Appunti: Lezione 15',
    preview: 'Neuroni e sinapsi - Trasmissione dell\'impulso nervoso...',
    type: 'note'
  },
  {
    id: 'exam-jan-15',
    title: '🧪 Esame: 15 Gennaio',
    preview: 'Anatomia I - Preparazione in corso (78% completato)',
    type: 'exam'
  }
];

interface RightSidebarProps {
  tools?: Tool[];
  contextItems?: ContextItem[];
  onToolSelect?: (toolId: string) => void;
  onContextSelect?: (contextId: string) => void;
}

const RightSidebar: React.FC<RightSidebarProps> = ({
  tools = defaultTools,
  contextItems = defaultContext,
  onToolSelect,
  onContextSelect,
}) => {
  const handleContextClick = (itemId: string) => {
    console.log(`Apertura documento: ${itemId}`);
    onContextSelect?.(itemId);
  };

  return (
    <SidebarContainer>
      <Section>
        <SectionTitle>Strumenti Attivi</SectionTitle>
        <ToolsPanel>
          {tools.map((tool) => (
            <ToolItem
              key={tool.id}
              onClick={() => onToolSelect?.(tool.id)}
            >
              <ToolIcon>{tool.icon}</ToolIcon>
              <ToolInfo>
                <ToolName>{tool.name}</ToolName>
                <ToolDescription>{tool.description}</ToolDescription>
              </ToolInfo>
            </ToolItem>
          ))}
        </ToolsPanel>
      </Section>

      <Section>
        <SectionTitle>Contesto Attuale</SectionTitle>
        <ContextPanel>
          {contextItems.map((item) => (
            <ContextItemWrapper key={item.id} onClick={() => handleContextClick(item.id)}>
              <ContextItemContainer>
                <ContextTitle>{item.title}</ContextTitle>
                <ContextPreview>{item.preview}</ContextPreview>
              </ContextItemContainer>
            </ContextItemWrapper>
          ))}
        </ContextPanel>
      </Section>
    </SidebarContainer>
  );
};

export default RightSidebar;
export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  toolsUsed?: string[];
}

export interface Chat {
  id: string;
  title: string;
  preview: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  icon: string;
  isActive: boolean;
}

export interface ContextItem {
  id: string;
  title: string;
  preview: string;
  type: 'document' | 'note' | 'exam';
}

export interface ApiConfig {
  baseUrl: string;
  wsUrl: string;
  apiKey?: string;
}

export interface User {
  id: string;
  username: string;
  displayName: string;
  avatar?: string;
}

export type ChatMode = 'normal' | 'study' | 'problem-solving' | 'data-analysis';
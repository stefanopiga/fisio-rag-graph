import { useState, useEffect, useCallback } from 'react';
import { GlobalStyle } from './styles/GlobalStyles';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import MainContent from './components/MainContent';
import RightSidebar from './components/RightSidebar';
import { Chat, Message, ChatMode } from './types';
import { useWebSocket } from './hooks/useWebSocket';
import { useAuth } from './hooks/useAuth';
import { config } from './config';
import { initRemoteLogger, cleanupRemoteLogger } from './utils/logger';
import { v4 as uuidv4 } from 'uuid';
import LoginPage from './components/LoginPage';

function App() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected' | 'error'>('disconnected');
  const [currentStreamingMessageId, setCurrentStreamingMessageId] = useState<string | null>(null);
  const { token, logout } = useAuth();

  // Enhanced debug logging for authentication state
  console.log('[APP_DEBUG] App component rendered with auth state:', { 
    hasToken: !!token, 
    tokenLength: token?.length,
    isAuthenticated: !!token,
    tokenPreview: token?.substring(0, 20) + '...' 
  });

  // Show login page if user is not authenticated
  if (!token) {
    console.log('[APP_DEBUG] No token found, showing LoginPage');
    return <LoginPage />;
  }

  console.log('[APP_DEBUG] Token found, rendering main app');

  // Initialize remote logger on app start
  useEffect(() => {
    initRemoteLogger();
    return () => {
      cleanupRemoteLogger();
    };
  }, []);

  // Helper function per gestire messaggi streaming
  const updateStreamingMessage = useCallback((content: string) => {
    if (!activeChat || !currentStreamingMessageId) return;

    setChats(prev => prev.map(chat => 
      chat.id === activeChat 
        ? {
            ...chat,
            messages: chat.messages.map(msg =>
              msg.id === currentStreamingMessageId
                ? { ...msg, content: msg.content + content }
                : msg
            ),
            updatedAt: new Date()
          }
        : chat
    ));
  }, [activeChat, currentStreamingMessageId]);

  // Helper function per creare un nuovo messaggio di risposta
  const createAssistantMessage = useCallback((chatId: string): Message => {
    const messageId = `assistant-${Date.now()}`;
    const newMessage: Message = {
      id: messageId,
      content: '',
      role: 'assistant',
      timestamp: new Date()
    };

    // Aggiungi il messaggio vuoto alla chat
    setChats(prev => prev.map(chat => 
      chat.id === chatId 
        ? { 
            ...chat, 
            messages: [...chat.messages, newMessage],
            updatedAt: new Date()
          }
        : chat
    ));

    setCurrentStreamingMessageId(messageId);
    return newMessage;
  }, []);

  const handleMessage = useCallback((response: any) => {
    console.log('WebSocket response received:', response);
    const messageData = response.data || {};
    
    if (response.type === 'connected') {
        // Gestisci messaggio di conferma connessione
        console.log('WebSocket connection confirmed:', messageData.message || 'Connected');
        setConnectionStatus('connected');
    } else if (response.type === 'session' && messageData.session_id) {
        // Potremmo voler gestire il session_id qui in futuro
    } else if (response.type === 'text' && messageData.content) {
        updateStreamingMessage(messageData.content);
    } else if (response.type === 'tools') {
        // Logica per gestire i tool (da implementare)
        console.log('Tool call received:', messageData);
    } else if (response.type === 'contexts') {
        // Logica per gestire i contesti (da implementare)
        console.log('Context received:', messageData);
    } else if (response.type === 'completed') {
        setIsLoading(false);
        setCurrentStreamingMessageId(null);
        console.log('Streaming completed');
    } else if (response.type === 'error') {
        console.error('WebSocket error:', messageData.error || 'Unknown error');
        setIsLoading(false);
        setCurrentStreamingMessageId(null);
    } else {
        // Log per messaggi non gestiti per debug
        console.log('Unhandled WebSocket message type:', response.type, response);
    }
  }, [activeChat, updateStreamingMessage]);

  const handleConnect = useCallback(() => {
    console.log('WebSocket connected');
    setConnectionStatus('connected');
  }, []);

  const handleDisconnect = useCallback(() => {
    console.log('WebSocket disconnected');
    setConnectionStatus('disconnected');
  }, []);

  const handleError = useCallback((error: any) => {
    console.error('WebSocket error:', error);
    setConnectionStatus('error');
  }, []);


  // Enhanced debug logging for WebSocket connection setup
  console.log('[APP_DEBUG] Setting up WebSocket with parameters:', {
    url: config.websocketUrl,
    sessionId: activeChat,
    hasToken: !!token,
    tokenLength: token?.length,
    tokenPreview: token?.substring(0, 20) + '...'
  });

  // WebSocket integration per comunicazione real-time
  const {
    isConnected,
    isConnecting,
    error: wsError,
    sendChat,
    reconnect
  } = useWebSocket({
    url: config.websocketUrl,
    sessionId: activeChat,
    token: token,
    onMessage: handleMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError
  });

  // Update connection status based on WebSocket state
  useEffect(() => {
    if (isConnecting) {
      setConnectionStatus('connecting');
    } else if (isConnected) {
      setConnectionStatus('connected');
    } else if (wsError) {
      setConnectionStatus('error');
    } else {
      setConnectionStatus('disconnected');
    }
  }, [isConnected, isConnecting, wsError]);

  const handleNewChat = () => {
    const newChat: Chat = {
      id: uuidv4(),
      title: 'Nuova Conversazione',
      preview: '',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    setChats(prev => [newChat, ...prev]);
    setActiveChat(newChat.id);
  };

  // Inizializza con una chat vuota se non ce ne sono
  useEffect(() => {
    if (chats.length === 0) {
      handleNewChat();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChatSelect = (chatId: string) => {
    setActiveChat(chatId);
  };

  const handleSendMessage = async (content: string, _mode: ChatMode) => {
    if (!activeChat) return;

    const newMessage: Message = {
      id: uuidv4(),
      content,
      role: 'user',
      timestamp: new Date()
    };

    // Aggiungi messaggio utente
    setChats(prev => prev.map(chat => 
      chat.id === activeChat 
        ? { 
            ...chat, 
            messages: [...chat.messages, newMessage],
            updatedAt: new Date()
          }
        : chat
    ));

    setIsLoading(true);

    // Controlla se WebSocket è connesso
    if (!isConnected) {
      console.warn('WebSocket not connected, attempting to reconnect...');
      reconnect();
      setIsLoading(false);
      return;
    }

    try {
      // Crea messaggio assistant vuoto per streaming
      createAssistantMessage(activeChat);
      
      // Invia messaggio via WebSocket
      sendChat(content, config.chat.defaultSearchType);
      
      console.log('Message sent via WebSocket:', content);
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      setCurrentStreamingMessageId(null);
    }
  };

  const handleToolSelect = (toolId: string) => {
    console.log('Tool selected:', toolId);
  };

  const currentChat = chats.find(chat => chat.id === activeChat);

  return (
    <>
      <GlobalStyle />
      <div style={{ display: 'grid', gridTemplateColumns: '18rem 1fr 20rem', gridTemplateRows: 'auto 1fr', height: '100vh', gap: '1px', backgroundColor: '#374151' }}>
        <Header 
          connectionStatus={connectionStatus}
          onReconnect={reconnect}
          onLogout={logout}
        />
        <Sidebar 
          chats={chats}
          activeChat={activeChat}
          onChatSelect={handleChatSelect}
          onNewChat={handleNewChat}
        />
        <MainContent
          messages={currentChat?.messages || []}
          chatTitle={currentChat?.title || 'Seleziona una chat'}
          currentModel="GPT-4 Turbo"
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
        <RightSidebar onToolSelect={handleToolSelect} />
      </div>
    </>
  );
}

export default App;
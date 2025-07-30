// Application configuration
export const config = {
  // API Configuration
  apiBaseUrl: 'http://127.0.0.1:8058',
  websocketUrl: 'ws://127.0.0.1:8058/ws',
  
  // Application Configuration
  appName: 'Fisio RAG Assistant',
  appVersion: '1.0.0',
  
  // Development Settings
  devMode: true,
  logLevel: 'info',
  
  // WebSocket Configuration
  websocket: {
    autoReconnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    pingInterval: 30000
  },
  
  // Chat Configuration
  chat: {
    defaultSearchType: 'hybrid' as const,
    maxMessageLength: 2000,
    typingIndicatorDelay: 1000
  },
  
  // UI Configuration
  ui: {
    animationDuration: 200,
    debounceDelay: 300,
    toastDuration: 5000
  }
} as const;

export type Config = typeof config; 
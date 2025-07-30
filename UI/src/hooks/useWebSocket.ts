import { useEffect, useRef, useState, useCallback } from 'react';
import { config } from '../config'; // Importa la configurazione
import { useDebugLogger } from '../utils/debugLogger';

interface WebSocketMessage {
  type: 'chat' | 'search' | 'ping' | 'error' | 'connect' | 'disconnect';
  data: Record<string, any>;
  session_id?: string;
  user_id?: string;
  timestamp?: string;
}

interface WebSocketResponse {
  type: 'message' | 'chunk' | 'tool_call' | 'error' | 'completed' | 'connected';
  data: Record<string, any>;
  session_id?: string;
  request_id?: string;
  timestamp?: string;
}

interface UseWebSocketProps {
  url: string;
  sessionId?: string;
  token?: string | null;
  onMessage: (data: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: Error | null;
  sendMessage: (message: Omit<WebSocketMessage, 'timestamp'>) => void;
  sendChat: (message: string, searchType?: string) => void;
  sendSearch: (query: string, searchType?: string, limit?: number) => void;
  disconnect: () => void;
  reconnect: () => void;
}

export const useWebSocket = ({
  url,
  sessionId,
  token,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  autoReconnect = false,
  reconnectInterval = 3000
}: UseWebSocketProps): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  
  const { log, error: logError, logWebSocket } = useDebugLogger('useWebSocket');

  // Use refs to store handlers, preventing connect from being recreated
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef((error: string) => {
    setError(new Error(error));
  });
  const onConnectRef = useRef(onConnect);
  const onDisconnectRef = useRef(onDisconnect);

  useEffect(() => {
    onMessageRef.current = onMessage;
    onErrorRef.current = (error: string) => {
      setError(new Error(error));
      onError?.(error); // Call the provided onError callback
    };
    onConnectRef.current = onConnect;
    onDisconnectRef.current = onDisconnect;
  }, [onMessage, onConnect, onDisconnect, onError]);


  const connect = useCallback(() => {
    console.log('[WEBSOCKET_DEBUG] connect() called with parameters:', {
      hasToken: !!token,
      tokenLength: token?.length,
      tokenType: typeof token,
      tokenValue: token === 'undefined' ? 'STRING_UNDEFINED' : (token === undefined ? 'ACTUAL_UNDEFINED' : 'VALID_TOKEN'),
      tokenPreview: token?.substring(0, 20) + '...',
      url,
      sessionId,
      currentState: websocketRef.current?.readyState
    });

    // CRITICAL: Prevent multiple simultaneous connections
    if (websocketRef.current && 
        (websocketRef.current.readyState === WebSocket.CONNECTING || 
         websocketRef.current.readyState === WebSocket.OPEN)) {
      console.log("[WEBSOCKET_DEBUG] Connection already exists, aborting new connection attempt");
      return;
    }

    if (!token) {
      console.log("[WEBSOCKET_DEBUG] No auth token, WebSocket connection aborted.");
      return;
    }

    if (token === 'undefined' || token === 'null') {
      console.error("[WEBSOCKET_DEBUG] Token is string 'undefined' or 'null', not a valid token!");
      return;
    }

    // Clean up any existing connection before creating new one
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }

    console.log('[WEBSOCKET_DEBUG] Attempting to connect to WebSocket...');
    setIsConnecting(true);
    setError(null);

    const wsUrl = `${url}?token=${token}${sessionId ? `&session_id=${sessionId}`: ''}`;
    console.log('[WEBSOCKET_DEBUG] Constructed WebSocket URL:', wsUrl);

    const socket = new WebSocket(wsUrl);
    websocketRef.current = socket;

    socket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setIsConnecting(false);
      if (onConnect) onConnect();
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        log('WebSocket message received', { type: data.type, hasData: !!data.data });
        logWebSocket('message_received', data);
        onMessage(data);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
        logError('Error parsing WebSocket message', err);
        onErrorRef.current?.('Error parsing message');
      }
    };

    socket.onclose = (event) => {
      console.log('WebSocket disconnected');
      log('WebSocket disconnected', { code: event.code, reason: event.reason });
      logWebSocket('close', { code: event.code, reason: event.reason });
      setIsConnected(false);
      setIsConnecting(false);
      if (onDisconnect) onDisconnect();

      // Auto-reconnect logic with exponential backoff
      if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current++;
        
        const backoffDelay = reconnectInterval * Math.pow(2, reconnectAttemptsRef.current - 1);
        console.log(`Attempting to reconnect... (${reconnectAttemptsRef.current}/${maxReconnectAttempts}) in ${backoffDelay}ms`);
        
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, backoffDelay);

      } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
        setError(new Error('Max reconnection attempts reached'));
        onErrorRef.current?.('Connection lost - max reconnection attempts reached');
      }
    };

    socket.onerror = (event) => {
      console.error('WebSocket error:', event);
      logError('WebSocket error occurred', event);
      logWebSocket('error', { message: 'Connection error' });
      setError(new Error('WebSocket connection failed'));
      setIsConnecting(false);
      onErrorRef.current?.('Connection error');
    };

  }, [url, sessionId, token, autoReconnect, reconnectInterval, log, logError, logWebSocket]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    
    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const sendMessage = useCallback((message: Omit<WebSocketMessage, 'timestamp'>) => {
    if (!websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      logError('Attempted to send message while disconnected');
      throw new Error('WebSocket is not connected');
    }
    
    const messageWithTimestamp: WebSocketMessage = {
      ...message,
      timestamp: new Date().toISOString()
    };
    
    console.log('Sending WebSocket message:', messageWithTimestamp);
    log('Sending WebSocket message', { type: message.type, hasData: !!message.data });
    logWebSocket('message_sent', messageWithTimestamp);
    
    websocketRef.current.send(JSON.stringify(messageWithTimestamp));
  }, [log, logError, logWebSocket]);

  const sendChat = useCallback((message: string, searchType: string = 'hybrid') => {
    sendMessage({
      type: 'chat',
      data: {
        message,
        search_type: searchType,
        metadata: {}
      }
    });
  }, [sendMessage]);

  const sendSearch = useCallback((query: string, searchType: string = 'hybrid', limit: number = 10) => {
    sendMessage({
      type: 'search',
      data: {
        query,
        search_type: searchType,
        limit,
        filters: {}
      }
    });
  }, [sendMessage]);

  const reconnect = useCallback(() => {
    console.log('[WEBSOCKET_DEBUG] Manual reconnect initiated');
    
    // Clear any pending auto-reconnect attempts to prevent race conditions
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
      console.log('[WEBSOCKET_DEBUG] Cleared pending auto-reconnect');
    }
    
    disconnect();
    reconnectAttemptsRef.current = 0;
    
    // Use direct call instead of setTimeout to avoid race conditions
    setTimeout(() => {
      console.log('[WEBSOCKET_DEBUG] Executing manual reconnect');
      connect();
    }, 1000);
  }, [disconnect, connect]);

  useEffect(() => {
    if (token) {
      connect();
    } else {
      // Disconnetti se il token non è più disponibile
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    }
    
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [connect, token]);

  // Ping to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      // Use websocketRef directly instead of sendMessage to avoid dependency issues
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        const pingMessage = {
          type: 'ping',
          data: {},
          timestamp: new Date().toISOString()
        };
        websocketRef.current.send(JSON.stringify(pingMessage));
        console.log('[WEBSOCKET_DEBUG] Ping sent');
      }
    }, 30000); // Ping every 30 seconds

    return () => clearInterval(pingInterval);
  }, [isConnected]); // Removed sendMessage dependency

  return {
    isConnected,
    isConnecting,
    error,
    sendMessage,
    sendChat,
    sendSearch,
    disconnect,
    reconnect
  };
}; 
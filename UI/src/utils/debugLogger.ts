// Frontend Debug Logger per React TypeScript
import { v4 as uuidv4 } from 'uuid';

interface LogEntry {
  timestamp: string;
  sessionId: string;
  requestId?: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  component: string;
  message: string;
  data?: any;
  error?: {
    message: string;
    stack?: string;
  };
}

class FrontendDebugLogger {
  private sessionId: string;
  private logs: LogEntry[] = [];
  private remoteLogEndpoint = '/api/frontend-logs';
  private batchSize = 10;
  private flushInterval = 5000; // 5 seconds
  private debugPanelEnabled = false;

  constructor() {
    this.sessionId = uuidv4();
    
    // Setup periodic flush
    setInterval(() => this.flushLogs(), this.flushInterval);
    
    // Intercept console methods
    this.interceptConsole();
    
    // Global error handler
    window.addEventListener('error', (event) => {
      this.log('error', 'window', 'Uncaught error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error?.stack
      });
    });
    
    // Unhandled promise rejection
    window.addEventListener('unhandledrejection', (event) => {
      this.log('error', 'window', 'Unhandled promise rejection', {
        reason: event.reason,
        promise: event.promise
      });
    });
  }
  private interceptConsole() {
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;
    
    console.log = (...args: any[]) => {
      this.log('info', 'console', args.join(' '));
      originalLog.apply(console, args);
    };
    
    console.error = (...args: any[]) => {
      this.log('error', 'console', args.join(' '));
      originalError.apply(console, args);
    };
    
    console.warn = (...args: any[]) => {
      this.log('warn', 'console', args.join(' '));
      originalWarn.apply(console, args);
    };
  }

  log(
    level: LogEntry['level'],
    component: string,
    message: string,
    data?: any,
    requestId?: string
  ) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      requestId,
      level,
      component,
      message,
      data
    };
    
    this.logs.push(entry);
    
    // Auto-flush if batch size reached
    if (this.logs.length >= this.batchSize) {
      this.flushLogs();
    }
    
    // Update debug panel if enabled
    if (this.debugPanelEnabled) {
      this.updateDebugPanel(entry);
    }
  }
  async flushLogs() {
    if (this.logs.length === 0) return;
    
    const logsToSend = [...this.logs];
    this.logs = [];
    
    try {
      await fetch(this.remoteLogEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs: logsToSend }),
      });
    } catch (error) {
      // If remote logging fails, at least log to console
      console.error('Failed to send logs to server:', error);
      console.log('Failed logs:', logsToSend);
    }
  }

  // WebSocket specific logging
  logWebSocketEvent(
    event: 'connect' | 'message_sent' | 'message_received' | 'error' | 'close',
    data: any,
    requestId?: string
  ) {
    this.log('info', 'websocket', `WebSocket ${event}`, data, requestId);
  }

  // Create debug panel overlay
  enableDebugPanel() {
    this.debugPanelEnabled = true;
    this.createDebugPanel();
  }
  private createDebugPanel() {
    const panel = document.createElement('div');
    panel.id = 'debug-panel';
    panel.style.cssText = `
      position: fixed;
      bottom: 0;
      right: 0;
      width: 400px;
      height: 300px;
      background: rgba(0, 0, 0, 0.9);
      color: #0f0;
      font-family: monospace;
      font-size: 12px;
      padding: 10px;
      overflow-y: auto;
      z-index: 99999;
      border: 1px solid #0f0;
    `;
    
    const header = document.createElement('div');
    header.innerHTML = `<strong>Debug Panel - Session: ${this.sessionId.slice(0, 8)}</strong>`;
    panel.appendChild(header);
    
    const logContainer = document.createElement('div');
    logContainer.id = 'debug-log-container';
    panel.appendChild(logContainer);
    
    document.body.appendChild(panel);
  }

  private updateDebugPanel(entry: LogEntry) {
    const container = document.getElementById('debug-log-container');
    if (!container) return;
    
    const logLine = document.createElement('div');
    const color = {
      debug: '#888',
      info: '#0f0',
      warn: '#ff0',
      error: '#f00'
    }[entry.level];
    
    logLine.style.color = color;
    logLine.textContent = `[${entry.timestamp.slice(11, 19)}] [${entry.component}] ${entry.message}`;
    
    if (entry.data) {
      const dataLine = document.createElement('pre');
      dataLine.style.marginLeft = '20px';
      dataLine.style.fontSize = '10px';
      dataLine.textContent = JSON.stringify(entry.data, null, 2);
      logLine.appendChild(dataLine);
    }
    
    container.appendChild(logLine);
    container.scrollTop = container.scrollHeight;
  }
}

export const debugLogger = new FrontendDebugLogger();

// Export hook for React components
export function useDebugLogger(component: string) {
  return {
    log: (message: string, data?: any) => 
      debugLogger.log('info', component, message, data),
    error: (message: string, error?: any) => 
      debugLogger.log('error', component, message, { error }),
    logWebSocket: (event: any, data: any, requestId?: string) =>
      debugLogger.logWebSocketEvent(event, data, requestId)
  };
}
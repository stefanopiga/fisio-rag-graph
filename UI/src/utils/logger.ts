import { config } from '../config';

type LogLevel = 'log' | 'info' | 'warn' | 'error';

interface LogPayload {
  level: LogLevel;
  message: string;
  timestamp: string;
  metadata?: any;
}

const originalConsole = {
  log: console.log,
  info: console.info,
  warn: console.warn,
  error: console.error,
};

let isLoggerActive = false;
const logQueue: LogPayload[] = [];
let sendTimeout: number | null = null;

async function sendLogsToServer(logs: LogPayload[]) {
  if (logs.length === 0) return;

  try {
    const body = JSON.stringify({ logs: logs });
    originalConsole.log('DEBUG: Sending logs with body:', body); // <-- LOG DI DEBUG

    await fetch(`${config.apiUrl}/log`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    });
  } catch (error) {
    originalConsole.error('Failed to send logs to server:', error);
  }
}

function flushQueue() {
  if (logQueue.length > 0) {
    sendLogsToServer([...logQueue]);
    logQueue.length = 0; // Clear the queue
  }
  if (sendTimeout) {
    clearTimeout(sendTimeout);
    sendTimeout = null;
  }
}

function handleLog(level: LogLevel, args: any[]) {
  const message = args
    .map((arg) => {
      try {
        if (typeof arg === 'string') return arg;
        return JSON.stringify(arg, null, 2);
      } catch (e) {
        return 'Unserializable object';
      }
    })
    .join(' ');

  const payload: LogPayload = {
    level,
    message,
    timestamp: new Date().toISOString(),
  };

  logQueue.push(payload);

  if (!sendTimeout) {
    sendTimeout = window.setTimeout(flushQueue, 2000); // Debounce for 2 seconds
  }
  
  // Also call the original console method
  originalConsole[level](...args);
}

export function initRemoteLogger() {
  // In a Vite project, use import.meta.env.DEV
  if (isLoggerActive || !import.meta.env.DEV) {
    return;
  }

  console.log = (...args: any[]) => handleLog('log', args);
  console.info = (...args: any[]) => handleLog('info', args);
  console.warn = (...args: any[]) => handleLog('warn', args);
  console.error = (...args: any[]) => handleLog('error', args);

  window.addEventListener('beforeunload', flushQueue);

  isLoggerActive = true;
  originalConsole.info('Remote logger initialized.');
}

export function cleanupRemoteLogger() {
  if (!isLoggerActive) return;

  flushQueue();
  window.removeEventListener('beforeunload', flushQueue);

  console.log = originalConsole.log;
  console.info = originalConsole.info;
  console.warn = originalConsole.warn;
  console.error = originalConsole.error;

  isLoggerActive = false;
  originalConsole.info('Remote logger cleaned up.');
} 
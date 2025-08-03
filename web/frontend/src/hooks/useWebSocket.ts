import { useEffect, useState, useRef } from 'react';
import io, { Socket } from 'socket.io-client';

interface WebSocketState {
  status: 'idle' | 'connecting' | 'connected' | 'running' | 'completed' | 'failed';
  progress: number;
  data: any;
  error: string | null;
}

export const useWebSocket = (workflowId: string | null) => {
  const [state, setState] = useState<WebSocketState>({
    status: 'idle',
    progress: 0,
    data: null,
    error: null,
  });
  
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    if (!workflowId) {
      return;
    }

    // Connect to WebSocket
    const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    const socket = io(WS_URL, {
      path: `/ws/workflows/${workflowId}`,
      transports: ['websocket'],
    });

    socketRef.current = socket;

    // Connection handlers
    socket.on('connect', () => {
      setState(prev => ({ ...prev, status: 'connected' }));
    });

    socket.on('disconnect', () => {
      setState(prev => ({ ...prev, status: 'idle' }));
    });

    // Message handlers
    socket.on('status', (data: any) => {
      setState(prev => ({
        ...prev,
        status: data.status || 'running',
        progress: data.progress || prev.progress,
      }));
    });

    socket.on('progress', (data: any) => {
      setState(prev => ({
        ...prev,
        status: 'running',
        progress: data.progress || prev.progress,
        data: data,
      }));
    });

    socket.on('completed', (data: any) => {
      setState(prev => ({
        ...prev,
        status: 'completed',
        progress: 100,
        data: data,
      }));
    });

    socket.on('error', (data: any) => {
      setState(prev => ({
        ...prev,
        status: 'failed',
        error: data.error || 'Unknown error',
        data: data,
      }));
    });

    // Cleanup
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, [workflowId]);

  return state;
};

// Alternative implementation using native WebSocket
export const useNativeWebSocket = (workflowId: string | null) => {
  const [state, setState] = useState<WebSocketState>({
    status: 'idle',
    progress: 0,
    data: null,
    error: null,
  });
  
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!workflowId) {
      return;
    }

    const WS_URL = process.env.REACT_APP_WS_URL?.replace('http', 'ws') || 'ws://localhost:8000';
    const ws = new WebSocket(`${WS_URL}/ws/workflows/${workflowId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setState(prev => ({ ...prev, status: 'connected' }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'status':
            setState(prev => ({
              ...prev,
              status: data.data.status || 'running',
              progress: data.data.progress || prev.progress,
            }));
            break;
            
          case 'progress':
            setState(prev => ({
              ...prev,
              status: 'running',
              progress: data.data.progress || prev.progress,
              data: data.data,
            }));
            break;
            
          case 'completed':
            setState(prev => ({
              ...prev,
              status: 'completed',
              progress: 100,
              data: data.data,
            }));
            break;
            
          case 'error':
            setState(prev => ({
              ...prev,
              status: 'failed',
              error: data.data.error || 'Unknown error',
              data: data.data,
            }));
            break;
        }
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    ws.onerror = (error) => {
      setState(prev => ({
        ...prev,
        status: 'failed',
        error: 'WebSocket connection error',
      }));
    };

    ws.onclose = () => {
      setState(prev => ({ ...prev, status: 'idle' }));
    };

    // Cleanup
    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      wsRef.current = null;
    };
  }, [workflowId]);

  return state;
};
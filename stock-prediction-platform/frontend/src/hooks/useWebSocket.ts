import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions {
  url?: string;
  onMessage?: (data: any) => void;
  autoConnect?: boolean;
  subscribeTicker?: string;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const defaultWsUrl = process.env.NEXT_PUBLIC_WS_URL || 
    (typeof window !== 'undefined' ? `ws://${window.location.hostname || 'localhost'}:8000/ws/stocks` : 'ws://localhost:8000/ws/stocks');

  const {
    url = defaultWsUrl,
    onMessage,
    autoConnect = true,
    subscribeTicker
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const onMessageRef = useRef(onMessage);
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;

        // Start ping heartbeat every 15s
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'ping' }));
          }
        }, 15000);

        // Subscribe to specific ticker if provided
        if (subscribeTicker) {
          ws.send(JSON.stringify({ action: 'subscribe', symbol: subscribeTicker }));
        }
      };

      ws.onmessage = (event) => {
        try {
          if (!event.data) return;
          // Sanitize NaN or Infinity tokens so JSON.parse never fails
          const cleanText = typeof event.data === 'string'
            ? event.data.replace(/:\s*NaN\b/g, ': 0.0').replace(/:\s*Infinity\b/g, ': null')
            : event.data;
          const data = typeof cleanText === 'string' ? JSON.parse(cleanText) : cleanText;
          if (data.type === 'PONG') return;
          setLastMessage(data);
          if (onMessageRef.current) {
            onMessageRef.current(data);
          }
        } catch (err) {
          console.warn("WebSocket parse deferred:", err);
        }
      };

      ws.onerror = () => {
        // WebSocket error events intentionally contain no details for browser security
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);

        // Exponential backoff reconnect: 1s, 2s, 4s, 8s... max 30s
        const delay = Math.min(30000, Math.pow(2, reconnectAttemptsRef.current) * 1000);
        reconnectAttemptsRef.current += 1;

        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (err) {
      console.warn("WebSocket connection attempt deferred:", err);
    }
  }, [url, subscribeTicker]);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => {
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        if (subscribeTicker && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ action: 'unsubscribe', symbol: subscribeTicker }));
        }
        wsRef.current.close();
      }
    };
  }, [connect, autoConnect, subscribeTicker]);

  const send = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }, []);

  return { isConnected, lastMessage, send, connect };
}

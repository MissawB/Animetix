import { useEffect, useRef, useState, useCallback } from 'react';
import { useToastStore } from '../store/toastStore';
import { logger } from '../utils/logger';

interface SocketData {
  type: string;
  state?: Record<string, unknown>;
  message?: Record<string, unknown>;
  action?: string;
}

const MAX_RECONNECT_ATTEMPTS = 5;
const INITIAL_RECONNECT_DELAY = 1000;

const useSocket = (roomCode: string | undefined, type: 'undercover' | 'codemanga') => {
  const [messages, setMessages] = useState<Record<string, unknown>[]>([]);
  const [gameState, setGameState] = useState<Record<string, unknown> | null>(null);
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const messageQueueRef = useRef<string[]>([]);
  const { addToast } = useToastStore();

  const connectRef = useRef<() => void>(() => {});

  const connect = useCallback(() => {
    if (!roomCode) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.host;
    const url = `${protocol}://${host}/ws/${type}/${roomCode}/`;

    logger.log(`Tentative de connexion WebSocket: ${url}`);
    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onopen = () => {
      logger.log(`Connecté à la room ${type}: ${roomCode}`);
      setConnected(true);
      setReconnecting(false);
      reconnectAttemptsRef.current = 0;
      
      if (reconnectAttemptsRef.current > 0) {
        addToast('Connexion rétablie !', 'success');
      }

      while (messageQueueRef.current.length > 0 && socket.readyState === WebSocket.OPEN) {
        const msg = messageQueueRef.current.shift();
        if (msg) socket.send(msg);
      }

      socket.send(JSON.stringify({ type: 'action', action: 'sync_state' }));
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as SocketData & Record<string, unknown>;
        if (data.type === 'game_state_update') {
          // Legacy shape (codemanga): full state under `state`.
          setGameState((data.state as Record<string, unknown>) || null);
        } else if (data.type === 'room_state') {
          // Undercover: state fields are at the top level — merge them in.
          const { type: _t, ...rest } = data;
          void _t;
          setGameState((prev) => ({ ...(prev || {}), ...rest }));
        } else if (data.type === 'private_role') {
          setGameState((prev) => ({ ...(prev || {}), private_role: data }));
        } else if (data.type === 'self_id') {
          setGameState((prev) => ({ ...(prev || {}), myId: data.id }));
        } else if (data.type === 'chat_message') {
          const msg = data.message || {};
          setMessages((prev) => [...prev, msg]);
          setGameState((prev) => ({
            ...(prev || {}),
            messages: [...(((prev?.messages as unknown[]) || [])), msg],
          }));
        }
      } catch (err) {
        console.error("Erreur de parsing WebSocket:", err);
      }
    };

    socket.onclose = (event) => {
      setConnected(false);
      
      if (event.code !== 1000) {
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          setReconnecting(true);
          const delay = INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current);
          
          if (reconnectAttemptsRef.current === 0) {
            addToast('Connexion perdue. Tentative de reconnexion...', 'info');
          }

          setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connectRef.current();
          }, delay);
        } else {
          setReconnecting(false);
          addToast('Impossible de se reconnecter. Vérifiez votre réseau.', 'error');
        }
      }
    };

    socket.onerror = (err) => {
      console.error("Erreur WebSocket:", err);
    };

  }, [roomCode, type, addToast]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    connect();
    return () => {
      if (socketRef.current) {
        socketRef.current.close(1000, "Component unmounted");
      }
    };
  }, [connect]);

  const sendAction = useCallback((action: string, payload = {}) => {
    const message = JSON.stringify({
      type: 'action',
      action,
      ...payload
    });

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(message);
    } else {
      console.warn("Socket non prêt. Message mis en file d'attente.");
      messageQueueRef.current.push(message);
      if (!reconnecting && !connected) {
        addToast('Action en attente de reconnexion...', 'info');
      }
    }
  }, [connected, reconnecting, addToast]);

  return { messages, gameState, connected, reconnecting, sendAction };
};

export default useSocket;

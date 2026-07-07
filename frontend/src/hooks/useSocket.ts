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

// Stable per-tab client id: survives a refresh (so the server reuses the same
// player slot and keeps the host) but differs across tabs. Without it, every
// reconnect span­ned a brand-new player.
const getClientId = (): string => {
  try {
    let id = sessionStorage.getItem('animetix_ws_cid');
    if (!id) {
      id = (crypto.randomUUID && crypto.randomUUID()) || `c_${Date.now()}_${Math.random().toString(36).slice(2)}`;
      sessionStorage.setItem('animetix_ws_cid', id);
    }
    return id;
  } catch {
    return `c_${Date.now()}_${Math.random().toString(36).slice(2)}`;
  }
};

const useSocket = (
  roomCode: string | undefined,
  type: 'undercover' | 'codemanga' | 'quizwho',
  extraQuery?: Record<string, string>,
) => {
  const clientIdRef = useRef<string>(getClientId());
  // Stringify once so the connect callback isn't recreated on every render.
  const extraQueryStr = extraQuery
    ? Object.entries(extraQuery)
        .filter(([, v]) => v != null && v !== '')
        .map(([k, v]) => `&${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
        .join('')
    : '';
  const [messages, setMessages] = useState<Record<string, unknown>[]>([]);
  const [gameState, setGameState] = useState<Record<string, unknown> | null>({ myId: getClientId() });
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
    const url = `${protocol}://${host}/ws/${type}/${roomCode}/?cid=${encodeURIComponent(clientIdRef.current)}${extraQueryStr}`;

    logger.log(`Tentative de connexion WebSocket: ${url}`);
    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onopen = () => {
      logger.log(`Connecté à la room ${type}: ${roomCode}`);
      setConnected(true);
      setReconnecting(false);
      
      if (reconnectAttemptsRef.current > 0) {
        addToast('Connexion rétablie !', 'success');
      }
      reconnectAttemptsRef.current = 0;


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
          // Legacy shape: full state under `state`.
          setGameState((data.state as Record<string, unknown>) || null);
        } else if (data.type === 'state') {
          // Code Manga: room fields under `room`, plus per-player my_role/my_team/my_id.
          const { type: _t, room, ...rest } = data;
          void _t;
          setGameState((prev) => ({ ...(prev || {}), ...((room as Record<string, unknown>) || {}), ...rest }));
        } else if (data.type === 'room_state') {
          // Undercover: state fields are at the top level — merge them in.
          const { type: _t, ...rest } = data;
          void _t;
          setGameState((prev) => ({ ...(prev || {}), ...rest }));
        } else if (data.type === 'private_role') {
          setGameState((prev) => ({ ...(prev || {}), private_role: data }));
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

  }, [roomCode, type, addToast, extraQueryStr]);

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

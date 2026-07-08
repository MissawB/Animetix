import { create } from 'zustand';
import { useToastStore } from './toastStore';
import { logger } from '../utils/logger';

const MAX_RECONNECT_ATTEMPTS = 5;
const INITIAL_RECONNECT_DELAY = 1000;

let reconnectTimeoutId: ReturnType<typeof setTimeout> | null = null;

interface NotificationStore {
  unreadCount: number;
  socket: WebSocket | null;
  isConnected: boolean;
  isReconnecting: boolean;
  reconnectAttempts: number;
  connect: () => void;
  disconnect: () => void;
  setUnreadCount: (count: number) => void;
  incrementUnread: () => void;
  clearUnread: () => void;
}

export const useNotificationStore = create<NotificationStore>((set, get) => ({
  unreadCount: 0,
  socket: null,
  isConnected: false,
  isReconnecting: false,
  reconnectAttempts: 0,

  setUnreadCount: (count) => set({ unreadCount: count }),
  incrementUnread: () => set((state) => ({ unreadCount: state.unreadCount + 1 })),
  clearUnread: () => set({ unreadCount: 0 }),

  connect: () => {
    // Only connect if not already connected/connecting
    if (get().socket || get().isConnected) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    // Proxied by Vite in dev, or straight to Django in prod
    const wsUrl = `${protocol}//${host}/ws/notifications/`;

    logger.log(`Connecting to notification socket: ${wsUrl}`);
    const socket = new WebSocket(wsUrl);
    set({ socket });

    socket.onopen = () => {
      logger.log('Notification socket connected');
      const { reconnectAttempts } = get();
      if (reconnectAttempts > 0) {
        useToastStore.getState().addToast('Connexion notifications rétablie !', 'success');
      }
      set({
        isConnected: true,
        isReconnecting: false,
        reconnectAttempts: 0,
        socket,
      });
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        logger.log('New real-time notification received:', data);

        // Show a toast
        const title = data.title || 'Nouvelle Notification';
        useToastStore.getState().addToast(title, 'info');

        // Increment badge
        get().incrementUnread();

        // Trigger a custom event so pages like NotificationsPage can invalidate react-query
        window.dispatchEvent(new CustomEvent('animetix:new_notification', { detail: data }));
      } catch (err) {
        console.error('Error parsing notification data', err);
      }
    };

    socket.onclose = (event) => {
      const code = event?.code ?? 1006;
      logger.log(`Notification socket closed with code ${code}`);
      set({ isConnected: false, socket: null });

      // Guard against reconnection on voluntary closes (code === 1000)
      if (code !== 1000) {
        const { reconnectAttempts } = get();
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          set({ isReconnecting: true });
          const delay = INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttempts);

          if (reconnectAttempts === 0) {
            useToastStore
              .getState()
              .addToast('Connexion notifications perdue. Tentative de reconnexion...', 'info');
          }

          if (reconnectTimeoutId) clearTimeout(reconnectTimeoutId);
          reconnectTimeoutId = setTimeout(() => {
            set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 }));
            get().connect();
          }, delay);
        } else {
          set({ isReconnecting: false });
          useToastStore
            .getState()
            .addToast(
              'Impossible de se connecter aux notifications. Vérifiez votre réseau.',
              'error',
            );
        }
      }
    };

    socket.onerror = (err) => {
      console.error('Notification socket error', err);
    };
  },

  disconnect: () => {
    const socket = get().socket;
    if (socket) {
      socket.close(1000, 'User logged out');
    }
    if (reconnectTimeoutId) {
      clearTimeout(reconnectTimeoutId);
      reconnectTimeoutId = null;
    }
    set({ socket: null, isConnected: false, isReconnecting: false, reconnectAttempts: 0 });
  },
}));

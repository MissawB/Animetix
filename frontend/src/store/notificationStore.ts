import { create } from 'zustand';
import { useToastStore } from './toastStore';

interface NotificationStore {
  unreadCount: number;
  socket: WebSocket | null;
  isConnected: boolean;
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

    console.log(`Connecting to notification socket: ${wsUrl}`);
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('Notification socket connected');
      set({ isConnected: true, socket });
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('New real-time notification received:', data);
        
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

    socket.onclose = () => {
      console.log('Notification socket closed');
      set({ isConnected: false, socket: null });
      // Retry connection after 5s
      setTimeout(() => {
        get().connect();
      }, 5000);
    };

    socket.onerror = (err) => {
      console.error('Notification socket error', err);
    };
  },

  disconnect: () => {
    const socket = get().socket;
    if (socket) {
      socket.close(1000, "User logged out");
      set({ socket: null, isConnected: false });
    }
  }
}));

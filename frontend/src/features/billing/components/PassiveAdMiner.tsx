import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../../../store/authStore';
import { useToastStore } from '../../../store/toastStore';
import { apiClient } from '../../../utils/apiClient';

export const PassiveAdMiner: React.FC = () => {
  const { user, refetchUser } = useAuthStore();
  const { addToast } = useToastStore();
  const [mineCount, setMineCount] = useState(0);

  useEffect(() => {
    // Ne miner que si l'utilisateur est connecté
    if (!user) return;

    // Intervalle de 3 minutes (180000 ms)
    const MINE_INTERVAL = 180000;

    const mineBx = async () => {
      try {
        const response = await apiClient('/api/v1/billing/wallet/mine/', {
          method: 'POST'
        });
        
        if (response.status === 'success') {
          // Silent refresh of the user to update the wallet balance
          await refetchUser();
          setMineCount(prev => prev + 1);
          
          // Optionally notify the user every few cycles to remind them they are earning
          if (mineCount > 0 && mineCount % 3 === 0) {
            addToast(`Minage passif : +${response.earned} Bx (Berrix) crédités !`, 'success');
          }
        }
      } catch (error) {
        console.error("Passive mining failed:", error);
        // Silently ignore cooldown errors to not spam the user
      }
    };

    const intervalId = setInterval(mineBx, MINE_INTERVAL);

    // Initial tick after 1 minute just to give them an early reward
    const initialTimeout = setTimeout(mineBx, 60000);

    return () => {
      clearInterval(intervalId);
      clearTimeout(initialTimeout);
    };
  }, [user, mineCount, refetchUser, addToast]);

  // Ce composant ne rend rien visuellement par défaut, il tourne en fond.
  return null;
};

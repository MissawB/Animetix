import React, { useEffect, useRef } from 'react';
import { useAuthStore } from '../../../store/authStore';
import { useToastStore } from '../../../store/toastStore';
import { apiClient } from '../../../utils/apiClient';
import { usePassiveMiningStore } from '../../../store/passiveMiningStore';

export const PassiveAdMiner: React.FC = () => {
  const { user, refetchUser } = useAuthStore();
  const { addToast } = useToastStore();
  const { 
    isEnabled, 
    setTimeLeft, 
    setStatus, 
    incrementTotalMined, 
    setLastMinedAt 
  } = usePassiveMiningStore();

  const isMiningRef = useRef(false);

  useEffect(() => {
    if (!user || !isEnabled) {
      setStatus('OFFLINE');
      return;
    }

    setStatus('ONLINE');
    const interval = setInterval(async () => {
      if (isMiningRef.current) return;

      const currentState = usePassiveMiningStore.getState();
      const currentTimeLeft = currentState.timeLeft;

      if (currentTimeLeft <= 1) {
        isMiningRef.current = true;
        setStatus('ONLINE'); // Processing / Mining
        try {
          const response = await apiClient('/api/v1/billing/wallet/mine/', {
            method: 'POST'
          });
          
          if (response.status === 'success') {
            await refetchUser();
            incrementTotalMined(response.earned);
            setLastMinedAt(new Date().toISOString());
            addToast(`Minage passif : +${response.earned} Bx (Berrix) crédités !`, 'success');
            setTimeLeft(180);
          }
        } catch (error) {
          console.error("Passive mining failed:", error);
          setStatus('COOLDOWN');
          setTimeLeft(60); // Check again in 60s
        } finally {
          isMiningRef.current = false;
        }
      } else {
        setTimeLeft(currentTimeLeft - 1);
      }
    }, 1000);

    return () => {
      clearInterval(interval);
    };
  }, [user, isEnabled, setTimeLeft, setStatus, incrementTotalMined, setLastMinedAt, refetchUser, addToast]);

  return null;
};


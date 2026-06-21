import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { akinetixService } from '../services/akinetixService';

export const useAkinetix = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['akinetix-state'];

  // Récupérer l'état du jeu (ou en démarrer un nouveau s'il n'y en a pas)
  const { data: gameState, isLoading: loading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      try {
        return await akinetixService.getState();
      } catch {
        return await akinetixService.startGame();
      }
    },
    refetchOnWindowFocus: false, // Évite de recharger l'état du jeu si on change d'onglet
  });

  // Gérer la réponse à une question
  const answerMutation = useMutation({
    mutationFn: akinetixService.submitAnswer,
    onSuccess: (newState) => {
      // Mettre à jour le cache directement avec la nouvelle réponse pour une UI instantanée
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  // Confirmer si la prédiction de l'IA est bonne
  const confirmMutation = useMutation({
    mutationFn: (isCorrect: boolean) => akinetixService.submitConfirmation(isCorrect),
    onSuccess: () => {
      // Invalider suffit à refetch un état de jeu propre (plus de full reload).
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  return { 
    gameState, 
    loading, 
    handleAnswer: answerMutation.mutate, 
    handleConfirm: confirmMutation.mutate 
  };
};


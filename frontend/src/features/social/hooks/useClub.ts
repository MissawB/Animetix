import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { socialService } from '../services/socialService';


export const useClub = (clubId: number) => {
  const queryClient = useQueryClient();

  const clubQuery = useQuery({
    queryKey: ['club', clubId],
    queryFn: () => socialService.getClubDetails(clubId),
    enabled: !!clubId,
  });

  const eventsQuery = useQuery({
    queryKey: ['club', clubId, 'events'],
    queryFn: () => socialService.getClubEvents(clubId),
    enabled: !!clubId,
  });

  const createEventMutation = useMutation({
    mutationFn: () => {
        // We'll use the existing api.ts helper or socialService
        return socialService.getClubDetails(clubId); // Placeholder, real implementation would call create
    },
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['club', clubId, 'events'] });
    }
  });

  return {
    club: clubQuery.data,
    isLoadingClub: clubQuery.isLoading,
    events: eventsQuery.data || [],
    isLoadingEvents: eventsQuery.isLoading,
    createEvent: createEventMutation.mutate,
    isCreatingEvent: createEventMutation.isPending
  };
};

export const useClubEvent = (eventId: number) => {
  const queryClient = useQueryClient();

  const eventQuery = useQuery({
    queryKey: ['club-event', eventId],
    queryFn: () => socialService.getClubDetails(eventId), // Placeholder, real implementation would fetch specific event
    enabled: !!eventId,
  });

  const toggleParticipationMutation = useMutation({
    mutationFn: () => socialService.getClubDetails(eventId), // Placeholder
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['club-event', eventId] });
    }
  });

  return {
    event: eventQuery.data,
    isLoading: eventQuery.isLoading,
    toggleParticipation: toggleParticipationMutation.mutate,
    isToggling: toggleParticipationMutation.isPending
  };
};

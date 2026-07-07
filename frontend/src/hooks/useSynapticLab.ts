import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../utils/apiClient';
import { UnifiedPlasticityState, PersonalizationFeatures, PlasticityResult } from '../types';

export function useSynapticLab() {
  // React Query Fetch Unified State
  const { data: state, isLoading, isError, refetch } = useQuery<UnifiedPlasticityState>({
    queryKey: ['singularity-lab-state'],
    queryFn: () => apiClient('/api/v1/singularity-lab/'),
  });

  // Local Form Config state
  const [tauPlus, setTauPlus] = useState(20.0);
  const [tauMinus, setTauMinus] = useState(20.0);
  const [mode, setMode] = useState<'auto' | 'manual'>('auto');
  const [manualArchetype, setManualArchetype] = useState('shonen_hero');
  const [intensityMult, setIntensityMult] = useState(1.0);
  const [features, setFeatures] = useState<PersonalizationFeatures>({
    aura: true,
    font: true,
    accent: true,
  });

  // Simulation parameters
  const [selectedSpikes, setSelectedSpikes] = useState<number[]>([]);
  const [lr, setLr] = useState(0.05);
  const [plasticityResult, setPlasticityResult] = useState<PlasticityResult | null>(null);

  // Sync parameters on data fetch
  const stateSig = state
    ? JSON.stringify({ c: state.plasticity_config, p: state.personalization_settings })
    : null;
  const [syncedSig, setSyncedSig] = useState<string | null>(null);
  if (state && stateSig !== syncedSig) {
    setSyncedSig(stateSig);
    setTauPlus(state.plasticity_config.tau_plus);
    setTauMinus(state.plasticity_config.tau_minus);
    setMode(state.personalization_settings.mode || 'auto');
    setManualArchetype(state.personalization_settings.manual_archetype || 'shonen_hero');
    setIntensityMult(state.personalization_settings.intensity_multiplier ?? 1.0);
    if (state.personalization_settings.features) {
      setFeatures(state.personalization_settings.features);
    }
  }

  // Mutations
  const configMutation = useMutation<UnifiedPlasticityState, Error, {
    action: string;
    tau_plus: number;
    tau_minus: number;
    mode: 'auto' | 'manual';
    manual_archetype: string;
    intensity_multiplier: number;
    features: PersonalizationFeatures;
  }>({
    mutationFn: (body) => 
      apiClient('/api/v1/singularity-lab/', { 
        method: 'POST', 
        body: JSON.stringify(body) 
      }),
    onSuccess: () => {
      refetch();
    }
  });

  const plasticityMutation = useMutation<PlasticityResult, Error, { action: string; learning_rate: number; trigger_spikes: number[] }>({
    mutationFn: (body) => 
      apiClient('/api/v1/singularity-lab/', { 
        method: 'POST', 
        body: JSON.stringify(body) 
      }),
    onSuccess: (data) => {
      setPlasticityResult(data);
      refetch();
    }
  });

  const handleApplyConfig = () => {
    configMutation.mutate({
      action: 'update_config',
      tau_plus: tauPlus,
      tau_minus: tauMinus,
      mode,
      manual_archetype: manualArchetype,
      intensity_multiplier: intensityMult,
      features
    });
  };

  const handleSimulate = () => {
    plasticityMutation.mutate({
      action: 'plasticity',
      learning_rate: lr,
      trigger_spikes: selectedSpikes
    });
  };

  const toggleSpike = (idx: number) => {
    if (selectedSpikes.includes(idx)) {
      setSelectedSpikes(selectedSpikes.filter(i => i !== idx));
    } else {
      setSelectedSpikes([...selectedSpikes, idx]);
    }
  };

  return {
    state,
    isLoading,
    isError,
    refetch,
    tauPlus, setTauPlus,
    tauMinus, setTauMinus,
    mode, setMode,
    manualArchetype, setManualArchetype,
    intensityMult, setIntensityMult,
    features, setFeatures,
    selectedSpikes, setSelectedSpikes,
    lr, setLr,
    plasticityResult, setPlasticityResult,
    configMutation,
    plasticityMutation,
    handleApplyConfig,
    handleSimulate,
    toggleSpike
  };
}
export type UseSynapticLabReturn = ReturnType<typeof useSynapticLab>;

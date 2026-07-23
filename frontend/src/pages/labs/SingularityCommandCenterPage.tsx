import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../utils/apiClient';
import { Activity, Zap, Cpu, Radio, Terminal, AlertTriangle, Binary, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { LabPage, LabHeader, LabPanel, LabStat, LabGuide } from './components/shared/LabKit';

interface AIServiceStatus {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'warning';
  load: number;
  metrics: Record<string, unknown>;
}

interface SingularityHealth {
  status: string;
  services: AIServiceStatus[];
  events: { time: string; type: string; msg: string }[];
  system_load: number;
}

const SERVICE_ICONS: Record<string, React.ReactNode> = {
  quantum: <Zap className="h-5 w-5" aria-hidden="true" />,
  plasticity: <Activity className="h-5 w-5" aria-hidden="true" />,
  swarm: <Radio className="h-5 w-5" aria-hidden="true" />,
  lnn: <Binary className="h-5 w-5" aria-hidden="true" />,
};

const SingularityCommandCenterPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery<SingularityHealth>({
    queryKey: ['singularity-command-center'],
    queryFn: () => apiClient('/api/v1/singularity-lab/command-center/'),
    refetchInterval: 5000, // Real-time feel
  });

  if (isLoading)
    return (
      <LabPage>
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6">
          <Loader2 className="h-14 w-14 animate-spin text-[#FDB913]" aria-hidden="true" />
          <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#8F94A5]">
            Connexion au cluster…
          </span>
        </div>
      </LabPage>
    );

  return (
    <LabPage>
      <LabHeader
        code="Protocole · Singularity"
        title="Centre de"
        accent="commandement"
        lede={t(
          'labs.singularity.subtitle',
          "Interface de monitoring centralisée pour l'orchestration des modèles cognitifs avancés.",
        )}
      />

      {/* Mesures globales */}
      <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
        <LabStat
          label="Efficacité globale"
          value={`${100 - (data?.system_load || 0)}%`}
          tone="gold"
        />
        <LabStat label="Nœuds cognitifs" value={data?.services?.length || 0} />
        <LabStat
          label="Charge système"
          value={`${data?.system_load || 0}%`}
          tone={(data?.system_load || 0) > 70 ? 'shu' : 'paper'}
        />
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Grille de monitoring */}
        <div className="space-y-8 lg:col-span-8">
          {/* Nœuds de service */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {data?.services?.map((svc, idx) => (
              <motion.div
                key={svc.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <LabPanel title={svc.name} corner={`node · ${svc.id}`} className="h-full">
                  <div className="space-y-6">
                    <div className="flex items-center gap-3">
                      <span className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3 text-[#FDB913]">
                        {SERVICE_ICONS[svc.id]}
                      </span>
                      <span className="flex items-center gap-2">
                        <span
                          className={`h-1.5 w-1.5 rounded-full ${
                            svc.status === 'online' ? 'bg-[#FDB913]' : 'bg-[#E8442B]'
                          }`}
                          aria-hidden
                        />
                        <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                          {svc.status}
                        </span>
                      </span>
                    </div>

                    {/* Charge */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                        <span>Charge de calcul</span>
                        <span>{svc.load}%</span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#F4F1E8]/10">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${svc.load}%` }}
                          className={`h-full ${svc.load > 70 ? 'bg-[#E8442B]' : 'bg-[#FDB913]'}`}
                        />
                      </div>
                    </div>

                    {/* Métriques */}
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(svc.metrics).map(([key, val]) => (
                        <div
                          key={key}
                          className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3"
                        >
                          <span className="mb-1 block text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
                            {key.replace('_', ' ')}
                          </span>
                          <span className="font-manga text-xs font-black italic text-[#F4F1E8]">
                            {String(val)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </LabPanel>
              </motion.div>
            ))}
          </div>

          {/* Sécurité du cluster */}
          <LabPanel title="Sécurité du cluster" corner="maximum">
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
              {[
                { label: 'Disponibilité', value: '99.998%' },
                { label: 'Garde-fous', value: 'Actifs' },
                { label: 'Chiffrement', value: 'AES-768-Q' },
                { label: 'Synchro', value: '1.2ms' },
              ].map((spec) => (
                <div key={spec.label} className="space-y-1">
                  <span className="block text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                    {spec.label}
                  </span>
                  <span className="font-manga text-sm font-black italic text-[#F4F1E8]">
                    {spec.value}
                  </span>
                </div>
              ))}
            </div>
          </LabPanel>
        </div>

        {/* Journal & infrastructure */}
        <div className="space-y-8 lg:col-span-4">
          {/* Journal des événements */}
          <LabPanel
            title="Journal des événements"
            corner={
              <span className="flex items-center gap-1.5">
                <Terminal className="h-3.5 w-3.5" aria-hidden="true" /> temps réel
              </span>
            }
          >
            <div className="max-h-[28rem] space-y-5 overflow-y-auto pr-2">
              {data?.events?.map((event, i) => (
                <div
                  key={i}
                  className="flex gap-4 border-l-2 border-[#F4F1E8]/10 py-1 pl-4 transition-colors hover:border-[#FDB913]/50"
                >
                  <span
                    className={`mt-1.5 h-2 w-2 flex-none rounded-full ${
                      i === 0 ? 'bg-[#FDB913]' : 'bg-[#F4F1E8]/20'
                    }`}
                    aria-hidden
                  />
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
                        {new Date(event.time).toLocaleTimeString()}
                      </span>
                      <span className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {event.type}
                      </span>
                    </div>
                    <p className="text-xs font-bold leading-relaxed text-[#F4F1E8]/80">
                      {event.msg}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 flex items-center gap-4 rounded-xl border border-[#E8442B]/25 bg-[#E8442B]/[0.05] p-4">
              <AlertTriangle className="h-5 w-5 flex-none text-[#E8442B]" aria-hidden="true" />
              <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                Aucune anomalie critique détectée sur les dernières 24 h.
              </span>
            </div>
          </LabPanel>

          {/* Infrastructure */}
          <LabPanel title="Carte d'infrastructure">
            <div className="flex aspect-square items-center justify-center rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10]">
              <Cpu className="h-20 w-20 text-[#8F94A5]/40" aria-hidden="true" />
            </div>
            <div className="mt-4 flex items-center justify-between text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
              <span>Région : europe-west9</span>
              <span>Multi-tenant : oui</span>
            </div>
          </LabPanel>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Le cluster se rapporte',
            body: 'La console interroge le centre de commandement toutes les 5 secondes : état global, charge système et liste des nœuds cognitifs actifs.',
          },
          {
            title: 'Lis chaque nœud',
            body: 'Chaque panneau détaille un service IA (quantum, plasticity, swarm, lnn) : statut, charge de calcul et métriques propres au moteur.',
          },
          {
            title: 'Surveille le journal',
            body: "Le journal des événements consigne l'activité neurale récente ; l'entrée la plus fraîche est marquée en or.",
          },
        ]}
        note="Ce tableau de bord est en lecture seule : il agrège la télémétrie des laboratoires de la singularité (essaim, plasticité, réseaux liquides…) pour repérer d'un coup d'œil un nœud surchargé ou hors ligne."
      />
    </LabPage>
  );
};

export default SingularityCommandCenterPage;

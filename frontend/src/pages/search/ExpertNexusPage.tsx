import React, { useState } from 'react';
import { Brain, Search, Zap } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '../../components/ui/Button';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import ExpertNexusPanel from './components/ExpertNexusPanel';

const ExpertNexusPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { t } = useTranslation();
  const initialQuery = searchParams.get('q') || '';

  const [query, setQuery] = useState(initialQuery);
  // Analyse initiale lancée dès le montage si on arrive avec ?q= (lien direct) :
  // runId démarre à 1, ce qui déclenche le panneau — pas d'effet de montage.
  const [activeQuery, setActiveQuery] = useState(initialQuery.trim());
  const [runId, setRunId] = useState(initialQuery.trim() ? 1 : 0);
  const [isStreaming, setIsStreaming] = useState(false);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearchParams({ q: query.trim() });
    setActiveQuery(query.trim());
    setRunId((n) => n + 1);
  };

  return (
    <AnimatedPage>
      <div className="min-h-screen w-full bg-[#0B0C10] text-[#F4F1E8]">
        <div className="mx-auto flex min-h-[calc(100vh-100px)] max-w-7xl flex-col px-6 py-12">
          <header className="relative mb-12 text-center">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-8 h-44"
              aria-hidden
            />
            <div className="relative mb-6 flex items-center justify-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                賢
              </span>
              <span className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                <Brain className="h-4 w-4 fill-current" /> RAG agentique SOTA · v2.0
              </span>
            </div>
            <h1 className="font-manga relative mb-4 text-5xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-7xl">
              EXPERT <span className="text-[#E8442B]">NEXUS</span>
            </h1>
            <p className="mx-auto max-w-2xl text-base font-medium leading-relaxed text-[#8F94A5]">
              Raisonnement arborescent multi-agents pour les requêtes complexes de Lore.
            </p>
          </header>

          <section className="mb-12 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8">
            <form onSubmit={onSubmit} className="flex gap-3">
              <div className="group relative flex-grow">
                <Search className="absolute left-5 top-1/2 h-6 w-6 -translate-y-1/2 text-[#8F94A5]/50 transition-colors group-focus-within:text-[#FDB913]" />
                <input
                  type="text"
                  aria-label="Rechercher"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t(
                    'search.expert.placeholder',
                    'Posez une question profonde sur un univers, une relation ou un arc narratif...',
                  )}
                  className="w-full rounded-2xl border border-[#F4F1E8]/15 bg-[#0B0C10] py-5 pl-14 pr-6 text-lg font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
                />
              </div>
              <Button
                type="submit"
                disabled={isStreaming || !query.trim()}
                className="rounded-2xl border-none !bg-[#E8442B] px-8 font-manga text-xl font-black uppercase italic !text-[#F4F1E8] transition-colors hover:!bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isStreaming ? (
                  <Zap className="h-6 w-6 animate-pulse" />
                ) : (
                  t('search.expert.solve_btn', 'RÉSOUDRE')
                )}
              </Button>
            </form>
          </section>

          <div className="flex-grow">
            <ExpertNexusPanel key={runId} query={activeQuery} onStreamingChange={setIsStreaming} />
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default ExpertNexusPage;

import React from 'react';
import { Search, Loader2, Star } from 'lucide-react';
import { VoiceProfile } from '../../../types';
import { LabPanel, LAB_INPUT } from './shared/LabKit';

/** Left "casting" sidebar: language filter, search, the voice-profile list
 *  (with the default Gemini-native option), and the active-profile card. The
 *  selection state lives in the page and is threaded in. */
export const S2SCastingSidebar: React.FC<{
  profilesData?: { results: VoiceProfile[] };
  isLoadingProfiles: boolean;
  searchQuery: string;
  setSearchQuery: (v: string) => void;
  langFilter: string;
  setLangFilter: (v: string) => void;
  selectedProfile: VoiceProfile | null;
  setSelectedProfile: (p: VoiceProfile | null) => void;
}> = ({
  profilesData,
  isLoadingProfiles,
  searchQuery,
  setSearchQuery,
  langFilter,
  setLangFilter,
  selectedProfile,
  setSelectedProfile,
}) => (
  <LabPanel title="Casting Persona" className="h-fit lg:col-span-4">
    <div className="space-y-6">
      <p className="text-sm leading-relaxed text-[#8F94A5]">
        Sélectionne une voix pour cloner la réponse de l'IA en temps réel.
      </p>

      {/* Language filter tab */}
      <div className="flex gap-1 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-1">
        {[
          { label: 'Tous', value: '' },
          { label: 'Seiyuu (JP)', value: 'japanese' },
          { label: 'VF (FR)', value: 'french' },
        ].map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setLangFilter(opt.value)}
            className={`flex-1 cursor-pointer rounded-lg border-none py-2 text-[9px] font-black uppercase tracking-wider transition-colors ${
              langFilter === opt.value
                ? 'bg-[#FDB913]/10 text-[#FDB913]'
                : 'bg-transparent text-[#8F94A5] hover:text-[#F4F1E8]'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8F94A5]"
          aria-hidden="true"
        />
        <input
          type="text"
          aria-label="Rechercher une voix"
          placeholder="Rechercher une voix..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className={`${LAB_INPUT} pl-10 text-xs`}
        />
      </div>

      {/* Profiles List */}
      <div className="custom-scrollbar max-h-[300px] space-y-2 overflow-y-auto pr-1">
        {/* Default Option (No profile) */}
        <button
          type="button"
          onClick={() => setSelectedProfile(null)}
          className={`flex w-full cursor-pointer items-center justify-between rounded-xl border px-4 py-3 text-left text-xs font-black transition-colors ${
            selectedProfile === null
              ? 'border-[#FDB913] bg-[#FDB913]/10 text-[#F4F1E8]'
              : 'border-[#F4F1E8]/10 bg-[#0B0C10] text-[#8F94A5] hover:border-[#F4F1E8]/25 hover:text-[#F4F1E8]'
          }`}
        >
          <div className="flex flex-col gap-0.5 truncate">
            <span>Gemini Native Voice</span>
            <span className="text-[8px] font-medium uppercase tracking-wide text-[#8F94A5]">
              Sans post-clonage RVC
            </span>
          </div>
          <span className="flex-none text-[8px] font-black uppercase tracking-widest text-[#FDB913]">
            Défaut
          </span>
        </button>

        {isLoadingProfiles ? (
          <div className="py-10 text-center">
            <Loader2 className="mx-auto h-6 w-6 animate-spin text-[#FDB913]" />
          </div>
        ) : profilesData?.results && profilesData.results.length > 0 ? (
          profilesData.results.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setSelectedProfile(p)}
              className={`flex w-full cursor-pointer items-center justify-between rounded-xl border px-4 py-3 text-left text-xs font-black transition-colors ${
                selectedProfile?.id === p.id
                  ? 'border-[#FDB913] bg-[#FDB913]/10 text-[#F4F1E8]'
                  : 'border-[#F4F1E8]/10 bg-[#0B0C10] text-[#8F94A5] hover:border-[#F4F1E8]/25 hover:text-[#F4F1E8]'
              }`}
            >
              <div className="flex flex-col gap-0.5 truncate pr-2">
                <span className="truncate">{p.name}</span>
                <span className="truncate text-[8px] font-medium uppercase tracking-wide text-[#8F94A5]">
                  {p.roles || 'Doubleur'}
                </span>
              </div>
              <span className="flex-none text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
                {p.language === 'japanese' ? '🇯🇵 JP' : p.language === 'french' ? '🇫🇷 FR' : '🌐'}
              </span>
            </button>
          ))
        ) : (
          <div className="py-10 text-center">
            <span className="text-[10px] font-black uppercase text-[#8F94A5]">
              Aucune voix trouvée
            </span>
          </div>
        )}
      </div>

      {selectedProfile && (
        <div className="space-y-2 rounded-xl border border-[#FDB913]/25 bg-[#FDB913]/[0.05] p-4">
          <span className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
            <Star className="h-3 w-3 fill-current" aria-hidden="true" /> Acteur actif
          </span>
          <h4 className="text-sm font-black uppercase text-[#F4F1E8]">{selectedProfile.name}</h4>
          <p className="text-[11px] italic leading-relaxed text-[#8F94A5]">
            «{' '}
            {selectedProfile.definition ||
              'Profil vocal configuré pour le doublage conversationnel.'}{' '}
            »
          </p>
        </div>
      )}
    </div>
  </LabPanel>
);

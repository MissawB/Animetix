import React from 'react';
import { User, Search, Loader2, Star } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { VoiceProfile } from '../../../types';

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
  <Card
    padding="lg"
    className="lg:col-span-4 h-fit bg-gray-900/40 border-white/5 shadow-2xl space-y-6"
  >
    <div>
      <h3 className="text-xs font-black uppercase opacity-40 mb-4 tracking-widest flex items-center gap-2">
        <User className="w-4 h-4" /> Casting Persona
      </h3>
      <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">
        Sélectionnez une voix pour cloner la réponse de l'IA en temps réel.
      </p>
    </div>

    {/* Language filter tab */}
    <div className="flex gap-1 bg-black/40 p-1 rounded-xl border border-white/5">
      {[
        { label: 'Tous', value: '' },
        { label: 'Seiyuu (JP)', value: 'japanese' },
        { label: 'VF (FR)', value: 'french' },
      ].map((opt) => (
        <button
          key={opt.value}
          onClick={() => setLangFilter(opt.value)}
          className={`flex-1 py-2 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all ${
            langFilter === opt.value
              ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
              : 'text-white/40 hover:text-white border border-transparent'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>

    {/* Search Input */}
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
      <input
        type="text"
        aria-label="Rechercher une voix"
        placeholder="Rechercher une voix..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="w-full bg-black/40 border border-white/5 rounded-xl pl-10 pr-4 py-3 font-bold text-xs outline-none focus:border-blue-500/50"
      />
    </div>

    {/* Profiles List */}
    <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1 custom-scrollbar">
      {/* Default Option (No profile) */}
      <button
        onClick={() => setSelectedProfile(null)}
        className={`w-full px-4 py-3 rounded-xl text-left text-xs font-black transition-all border flex items-center justify-between group ${
          selectedProfile === null
            ? 'border-blue-500 bg-blue-500/10 text-white shadow-lg'
            : 'border-white/5 bg-black/25 text-white/50 hover:border-white/10 hover:text-white'
        }`}
      >
        <div className="flex flex-col gap-0.5 truncate">
          <span>Gemini Native Voice</span>
          <span className="text-[8px] opacity-40 font-medium uppercase tracking-wide">
            Sans post-clonage RVC
          </span>
        </div>
        <Badge variant="neutral" className="text-[7px] font-black uppercase bg-black/40">
          ⚡ DEFAULT
        </Badge>
      </button>

      {isLoadingProfiles ? (
        <div className="py-10 text-center">
          <Loader2 className="w-6 h-6 animate-spin mx-auto text-blue-500" />
        </div>
      ) : profilesData?.results && profilesData.results.length > 0 ? (
        profilesData.results.map((p) => (
          <button
            key={p.id}
            onClick={() => setSelectedProfile(p)}
            className={`w-full px-4 py-3 rounded-xl text-left text-xs font-black transition-all border flex items-center justify-between group ${
              selectedProfile?.id === p.id
                ? 'border-blue-500 bg-blue-500/10 text-white shadow-lg'
                : 'border-white/5 bg-black/25 text-white/50 hover:border-white/10 hover:text-white'
            }`}
          >
            <div className="flex flex-col gap-0.5 truncate pr-2">
              <span className="truncate">{p.name}</span>
              <span className="text-[8px] opacity-40 truncate font-medium uppercase tracking-wide">
                {p.roles || 'Doubleur'}
              </span>
            </div>
            <Badge
              variant="neutral"
              className="text-[7px] font-black uppercase shrink-0 bg-black/40"
            >
              {p.language === 'japanese' ? '🇯🇵 JP' : p.language === 'french' ? '🇫🇷 FR' : '🌐'}
            </Badge>
          </button>
        ))
      ) : (
        <div className="py-10 text-center text-white/20">
          <span className="text-[10px] font-black uppercase">Aucune voix trouvée</span>
        </div>
      )}
    </div>

    {selectedProfile && (
      <Card padding="md" className="bg-blue-500/10 border-blue-500/20 text-blue-200 space-y-2">
        <span className="text-[8px] font-black uppercase tracking-wider text-blue-400 flex items-center gap-1">
          <Star className="w-3 h-3 fill-current text-blue-400" /> Acteur Actif
        </span>
        <h4 className="font-black text-sm uppercase">{selectedProfile.name}</h4>
        <p className="text-[10px] opacity-60 leading-relaxed italic">
          "
          {selectedProfile.definition || 'Profil vocal configuré pour le doublage conversationnel.'}
          "
        </p>
      </Card>
    )}
  </Card>
);

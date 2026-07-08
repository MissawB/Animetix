import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, EyeOff, Check, Vote, Ghost, Lock, Play } from 'lucide-react';
import { UPlayer } from '../../types';

interface UndercoverLobbySettingsProps {
  isHost: boolean;
  isPublic: boolean;
  categories: string[];
  difficulty: string;
  under: number;
  white: number;
  players: UPlayer[];
  civilsCount: number;
  maxUnderSlider: number;
  maxWhiteSlider: number;
  applySettings: (patch: Record<string, unknown>) => void;
  toggleCategory: (key: string) => void;
  sendAction: (action: string, payload?: Record<string, unknown>) => void;
  MIN_PLAYERS: number;
}

const DIFFS = ['Easy', 'Normal', 'Hard'];

export const UndercoverLobbySettings: React.FC<UndercoverLobbySettingsProps> = ({
  isHost,
  isPublic,
  categories,
  difficulty,
  under,
  white,
  players,
  civilsCount,
  maxUnderSlider,
  maxWhiteSlider,
  applySettings,
  toggleCategory,
  sendAction,
  MIN_PLAYERS,
}) => {
  const { t } = useTranslation();

  const CATEGORIES = useMemo(
    () => [
      { key: 'Anime', label: t('games.undercover.categories.anime', 'Anime'), anchor: true },
      { key: 'Manga', label: t('games.undercover.categories.manga', 'Manga'), anchor: true },
      {
        key: 'Character',
        label: t('games.undercover.categories.anime_characters', 'Persos anime'),
        anchor: true,
      },
      { key: 'Movie', label: t('games.undercover.categories.movies', 'Films') },
      { key: 'Game', label: t('games.undercover.categories.video_games', 'Jeux vidéo') },
      { key: 'Actor', label: t('games.undercover.categories.actors', 'Acteurs') },
      { key: 'VGChar', label: t('games.undercover.categories.game_characters', 'Persos de jeux') },
    ],
    [t],
  );

  const ANCHOR_KEYS = useMemo(
    () => CATEGORIES.filter((c) => c.anchor).map((c) => c.key),
    [CATEGORIES],
  );
  const hasAnchor = categories.some((c) => ANCHOR_KEYS.includes(c));

  const DIFF_LABEL: Record<string, string> = {
    Easy: t('games.undercover.difficulty.easy', 'Facile'),
    Normal: t('games.undercover.difficulty.normal', 'Normal'),
    Hard: t('games.undercover.difficulty.hard', 'Difficile'),
  };

  const DIFF_HINT: Record<string, string> = {
    Easy: t('games.undercover.difficulty.hint_easy', 'œuvres très populaires'),
    Normal: t('games.undercover.difficulty.hint_normal', 'œuvres connues'),
    Hard: t('games.undercover.difficulty.hint_hard', 'œuvres plus pointues'),
  };

  const sliderStyle = (
    value: number,
    min: number,
    max: number,
    accent: string,
  ): React.CSSProperties => {
    const pct = max > min ? ((value - min) / (max - min)) * 100 : 0;
    return {
      background: `linear-gradient(90deg, ${accent} 0%, ${accent} ${pct}%, rgba(255,255,255,0.08) ${pct}%, rgba(255,255,255,0.08) 100%)`,
      ['--uc-accent' as string]: accent,
    };
  };

  if (!isHost) {
    return (
      <div className="text-center py-8">
        <Globe className="w-8 h-8 text-white/20 mx-auto mb-3 animate-pulse" />
        <p className="opacity-40 italic">
          {t('games.undercover.room.waiting_host', "En attente du briefing par le chef d'unité…")}
        </p>
      </div>
    );
  }

  return (
    <>
      <div>
        <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">
          {t('games.undercover.room.visibility_label', 'Visibilité du salon')}
        </p>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => applySettings({ visibility: 'public' })}
            className={`flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${
              isPublic
                ? 'border-green-500 bg-green-500/15 text-green-400'
                : 'border-white/10 text-white/40 hover:border-green-500/40'
            }`}
          >
            <Globe className="w-3.5 h-3.5" /> {t('games.undercover.visibility.public', 'Public')}
          </button>
          <button
            onClick={() => applySettings({ visibility: 'private' })}
            className={`flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${
              !isPublic
                ? 'border-red-500 bg-red-500/15 text-red-400'
                : 'border-white/10 text-white/40 hover:border-red-500/40'
            }`}
          >
            <EyeOff className="w-3.5 h-3.5" /> {t('games.undercover.visibility.private', 'Privé')}
          </button>
        </div>
        <p className="mt-2 text-[11px] text-white/35 italic">
          {isPublic
            ? t(
                'games.undercover.room.public_hint',
                'Visible dans la liste des salons publics — tout le monde peut rejoindre.',
              )
            : t(
                'games.undercover.room.private_hint',
                "Accessible uniquement via le code ou l'URL.",
              )}
        </p>
      </div>

      <div>
        <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">
          {t('games.undercover.room.categories_label', 'Catégories à inclure')}
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {CATEGORIES.map((c) => {
            const on = categories.includes(c.key);
            return (
              <button
                key={c.key}
                onClick={() => toggleCategory(c.key)}
                className={`flex items-center gap-2 py-2.5 px-3 rounded-xl border-2 text-xs font-black uppercase transition-all ${
                  on
                    ? 'border-red-500 bg-red-500/15 text-red-400'
                    : 'border-white/10 text-white/40 hover:border-red-500/40'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded grid place-items-center border-2 shrink-0 ${
                    on ? 'bg-red-500 border-red-500' : 'border-white/25'
                  }`}
                >
                  {on && <Check className="w-3 h-3 text-white" />}
                </span>
                <span className="truncate">
                  {c.label}
                  {c.anchor && <span className="text-yellow-400/70"> ⚓</span>}
                </span>
              </button>
            );
          })}
        </div>
        <p className={`mt-2 text-[11px] italic ${hasAnchor ? 'text-white/35' : 'text-red-400'}`}>
          {t(
            'games.undercover.room.anchor_hint',
            '⚓ Au moins une catégorie ancre (anime/manga/perso) doit être cochée — chaque paire en garde un mot.',
          )}
        </p>
      </div>

      <div>
        <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">
          {t('games.undercover.room.difficulty_label', 'Difficulté · popularité')}
        </p>
        <div className="grid grid-cols-3 gap-2">
          {DIFFS.map((d) => (
            <button
              key={d}
              onClick={() => applySettings({ difficulty: d })}
              className={`py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${
                difficulty === d
                  ? 'border-red-500 bg-red-500/15 text-red-400'
                  : 'border-white/10 text-white/40 hover:border-red-500/40'
              }`}
            >
              {DIFF_LABEL[d]}
            </button>
          ))}
        </div>
        <p className="mt-2 text-[11px] text-white/35 italic">
          {DIFF_HINT[difficulty]}{' '}
          {t(
            'games.undercover.room.difficulty_hint_suffix',
            "— plus c'est dur, plus les œuvres sont obscures.",
          )}
        </p>
      </div>

      <div className="space-y-6">
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <p className="text-[11px] font-black uppercase tracking-[0.25em] text-red-400/80 flex items-center gap-1.5">
              <Vote className="w-3.5 h-3.5" />{' '}
              {t('games.undercover.room.intruders_label', 'Intrus')}
            </p>
            <span className="min-w-9 text-center px-2.5 py-1 rounded-lg bg-red-500/15 text-red-400 text-base font-black tabular-nums shadow-[0_0_14px_-4px_rgba(239,68,68,0.6)]">
              {under}
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={maxUnderSlider}
            value={under}
            onChange={(e) => applySettings({ num_undercovers: Number(e.target.value) })}
            className="uc-slider"
            style={sliderStyle(under, 1, maxUnderSlider, '#ef4444')}
            aria-label={t('games.undercover.room.intruders_aria', "Nombre d'intrus")}
          />
          <div className="flex justify-between mt-1.5 text-[10px] font-bold text-white/25 tabular-nums">
            <span>1</span>
            <span>
              {t('games.undercover.room.max_value', {
                defaultValue: 'max {{value}}',
                value: maxUnderSlider,
              })}
            </span>
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <p className="text-[11px] font-black uppercase tracking-[0.25em] text-purple-300/80 flex items-center gap-1.5">
              <Ghost className="w-3.5 h-3.5" /> Mr. White
            </p>
            <span className="min-w-9 text-center px-2.5 py-1 rounded-lg bg-purple-500/15 text-purple-300 text-base font-black tabular-nums shadow-[0_0_14px_-4px_rgba(192,132,252,0.6)]">
              {white}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={maxWhiteSlider}
            value={white}
            onChange={(e) => applySettings({ num_mrwhites: Number(e.target.value) })}
            className="uc-slider"
            style={sliderStyle(white, 0, maxWhiteSlider, '#c084fc')}
            aria-label={t('games.undercover.room.mrwhite_aria', 'Nombre de Mr. White')}
          />
          <div className="flex justify-between mt-1.5 text-[10px] font-bold text-white/25 tabular-nums">
            <span>0</span>
            <span>
              {t('games.undercover.room.max_value', {
                defaultValue: 'max {{value}}',
                value: maxWhiteSlider,
              })}
            </span>
          </div>
          <p className="mt-2 text-[11px] text-white/35 italic">
            {t(
              'games.undercover.room.mrwhite_hint',
              "Le Mr. White n'a pas de mot : éliminé, il doit deviner celui des civils pour gagner.",
            )}
          </p>
        </div>
        <div>
          <div className="flex h-2.5 rounded-full overflow-hidden bg-white/5">
            {civilsCount > 0 && (
              <div
                className="bg-green-500/70"
                style={{ width: `${(civilsCount / Math.max(1, players.length)) * 100}%` }}
              />
            )}
            {under > 0 && (
              <div
                className="bg-red-500/70"
                style={{ width: `${(under / Math.max(1, players.length)) * 100}%` }}
              />
            )}
            {white > 0 && (
              <div
                className="bg-purple-400/70"
                style={{ width: `${(white / Math.max(1, players.length)) * 100}%` }}
              />
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2 mt-3 text-[11px] font-black uppercase tracking-wider">
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-green-500/10 text-green-400">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              {t('games.undercover.room.civils_count', {
                defaultValue: '{{count}} civils',
                count: civilsCount,
              })}
            </span>
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-500/10 text-red-400">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              {t('games.undercover.room.intruders_count', {
                defaultValue: '{{count}} intrus',
                count: under,
              })}
            </span>
            {white > 0 && (
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-300">
                <span className="w-2 h-2 rounded-full bg-purple-400" />
                {t('games.undercover.room.mrwhite_count', {
                  defaultValue: '{{count}} Mr. White',
                  count: white,
                })}
              </span>
            )}
          </div>
        </div>
      </div>

      <div>
        <button
          onClick={() => sendAction('start_game')}
          disabled={players.length < MIN_PLAYERS || !hasAnchor}
          className="w-full py-4 rounded-2xl bg-red-600 enabled:hover:bg-red-500 text-white font-black italic uppercase tracking-widest text-lg shadow-[0_10px_30px_-10px_rgba(239,68,68,0.7)] transition-all enabled:hover:scale-[1.01] active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Play className="w-5 h-5 fill-current" />{' '}
          {t('games.undercover.room.start_button', 'Lancer la mission')}
        </button>
        {players.length < MIN_PLAYERS && (
          <p className="mt-3 text-center text-[11px] font-bold uppercase tracking-widest text-white/35 flex items-center justify-center gap-1.5">
            <Lock className="w-3.5 h-3.5" />{' '}
            {t('games.undercover.room.min_players_hint', {
              defaultValue: 'Min. {{count}} agents — partage le code ci-dessus',
              count: MIN_PLAYERS,
            })}
          </p>
        )}
        {players.length >= MIN_PLAYERS && !hasAnchor && (
          <p className="mt-3 text-center text-[11px] font-bold uppercase tracking-widest text-red-400 flex items-center justify-center gap-1.5">
            <Lock className="w-3.5 h-3.5" />{' '}
            {t(
              'games.undercover.room.anchor_required',
              'Coche au moins une catégorie ancre (anime/manga/perso)',
            )}
          </p>
        )}
      </div>
    </>
  );
};

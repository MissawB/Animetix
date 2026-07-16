import React from 'react';
import { useTranslation } from 'react-i18next';
import { Play, Pause, Music } from 'lucide-react';
import { HintType } from '../hooks/useBlindtestGame';

export interface BlindtestPlayerProps {
  videoUrl: string;
  hintsEnabled: boolean;
  showVisual: boolean;
  hintType: HintType;
  hintLevel: number;
  aspect: number;
  setAspect: (val: number) => void;
  isPlaying: boolean;
  setIsPlaying: (val: boolean) => void;
  mediaRef: React.RefObject<HTMLVideoElement | null>;
  togglePlay: () => void;
  currentMode: 'OP' | 'ED';
  attemptsLeft?: number;
}

const filterFor = (type: HintType, level: number): string => {
  const L = Math.max(0, Math.min(1, level));
  const blur = `blur(${(3 + L * 13).toFixed(1)}px)`;
  switch (type) {
    case 'invert':
      return `invert(1) ${blur}`;
    case 'grayscale':
      return `grayscale(1) contrast(1.15) ${blur}`;
    case 'hue':
      return `hue-rotate(160deg) saturate(2.5) ${blur}`;
    case 'blur':
      return `blur(${(6 + L * 18).toFixed(1)}px)`;
    case 'noise':
      return `${blur} brightness(0.9)`;
    default:
      return blur;
  }
};

export const BlindtestPlayer: React.FC<BlindtestPlayerProps> = ({
  videoUrl,
  hintsEnabled,
  showVisual,
  hintType,
  hintLevel,
  aspect,
  setAspect,
  isPlaying,
  setIsPlaying,
  mediaRef,
  togglePlay,
  currentMode,
  attemptsLeft,
}) => {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center py-8">
      {/* Current format */}
      <div className="mb-8">
        <span className="px-4 py-1.5 rounded-full bg-yellow-400/15 border border-yellow-400/30 text-yellow-600 dark:text-yellow-400 text-[11px] font-black uppercase tracking-widest">
          {currentMode === 'OP'
            ? t('games.blindtest.game.format_opening', 'Opening')
            : t('games.blindtest.game.format_ending', 'Ending')}
        </span>
      </div>

      {hintsEnabled ? (
        /* One persistent media element (audio stays continuous). The vinyl
           covers it until the first guess; afterwards the clip is revealed
           distorted — colour effect always on, blur easing each guess. */
        <div
          className="relative w-full max-w-lg rounded-3xl overflow-hidden shadow-2xl bg-[#0d0d12]"
          style={{ aspectRatio: String(aspect) }}
        >
          <video
            ref={mediaRef}
            src={videoUrl}
            className={`w-full h-full object-cover transition-all duration-500 ${showVisual ? 'opacity-100' : 'opacity-0'}`}
            style={{ filter: showVisual ? filterFor(hintType, hintLevel) : 'none' }}
            preload="auto"
            aria-label={t('games.blindtest.game.visual_hint_aria', 'Indice visuel du générique')}
            onLoadedMetadata={(e) => {
              const el = e.currentTarget;
              if (el.videoWidth && el.videoHeight) setAspect(el.videoWidth / el.videoHeight);
            }}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={() => setIsPlaying(false)}
            onEmptied={() => setIsPlaying(false)}
          >
            <track kind="captions" />
          </video>

          {showVisual && hintType === 'noise' && (
            <div
              className="absolute inset-0 mix-blend-overlay pointer-events-none"
              style={{
                backgroundImage: "url('/static/img/noise.png')",
                opacity: 0.4 + hintLevel * 0.5,
              }}
            />
          )}

          {!showVisual && (
            <div className="absolute inset-0 grid place-items-center">
              <div
                className={`relative w-44 h-44 rounded-full grid place-items-center shadow-[0_20px_50px_rgba(0,0,0,0.5)] ${isPlaying ? 'motion-safe:animate-[spin_4s_linear_infinite]' : ''}`}
                style={{
                  background:
                    'repeating-radial-gradient(circle at center, #0d0d12 0 3px, #1b1b24 3px 6px)',
                }}
              >
                <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-transparent via-white/5 to-white/15" />
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-300 to-orange-500 grid place-items-center border-4 border-black/40 shadow-inner">
                  <Music className="w-6 h-6 text-black/80" />
                </div>
                <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-[#0f0f1a] border border-white/20" />
              </div>
            </div>
          )}

          <button
            onClick={togglePlay}
            aria-label={
              isPlaying
                ? t('games.blindtest.game.pause_aria', 'Mettre en pause')
                : t('games.blindtest.game.play_aria', 'Lancer la lecture')
            }
            className="absolute inset-0 grid place-items-center group outline-none"
          >
            <span className="bg-black/60 backdrop-blur-sm text-white p-4 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              {isPlaying ? (
                <Pause className="w-7 h-7" />
              ) : (
                <Play className="w-7 h-7 fill-current" />
              )}
            </span>
          </button>
        </div>
      ) : (
        /* Vinyl disc — audio only (hints disabled) */
        <button
          onClick={togglePlay}
          aria-label={
            isPlaying
              ? t('games.blindtest.game.pause_aria', 'Mettre en pause')
              : t('games.blindtest.game.play_aria', 'Lancer la lecture')
          }
          className="group relative outline-none"
        >
          <div
            className={`relative w-60 h-60 rounded-full grid place-items-center shadow-[0_20px_50px_rgba(0,0,0,0.5)] ${isPlaying ? 'motion-safe:animate-[spin_4s_linear_infinite]' : ''}`}
            style={{
              background:
                'repeating-radial-gradient(circle at center, #0d0d12 0 3px, #1b1b24 3px 6px)',
            }}
          >
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-transparent via-white/5 to-white/15 pointer-events-none" />
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-yellow-300 to-orange-500 grid place-items-center border-4 border-black/40 shadow-inner">
              <Music className="w-9 h-9 text-black/80" />
            </div>
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-[#0f0f1a] border border-white/20" />
          </div>
          <span className="absolute inset-0 grid place-items-center pointer-events-none">
            <span className="bg-black/60 backdrop-blur-sm text-white p-5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              {isPlaying ? (
                <Pause className="w-8 h-8" />
              ) : (
                <Play className="w-8 h-8 fill-current" />
              )}
            </span>
          </span>
          <video
            ref={mediaRef}
            src={videoUrl}
            className="hidden"
            preload="auto"
            aria-label={t('games.blindtest.game.audio_clip_aria', 'Extrait audio du blind test')}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={() => setIsPlaying(false)}
            onEmptied={() => setIsPlaying(false)}
          >
            <track kind="captions" />
          </video>
        </button>
      )}

      <p className="mt-8 font-bold text-gray-500 uppercase tracking-widest text-xs">
        {isPlaying
          ? t('games.blindtest.game.playing', 'Lecture en cours…')
          : hintsEnabled
            ? t(
                'games.blindtest.game.listen_hint_visual',
                'Clique pour écouter — le visuel se précise à chaque essai',
              )
            : t('games.blindtest.game.listen_hint_disc', 'Cliquez sur le disque pour écouter')}
      </p>
      {typeof attemptsLeft === 'number' && (
        <p className="mt-2 text-[11px] font-black uppercase tracking-widest text-yellow-600 dark:text-yellow-400">
          {t('games.blindtest.game.attempts_left', {
            defaultValue: '{{count}} tentative{{plural}} restante{{plural}}',
            count: attemptsLeft,
            plural: attemptsLeft > 1 ? 's' : '',
          })}
        </p>
      )}
    </div>
  );
};

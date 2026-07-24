import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Target, Trophy, RotateCcw, AlertTriangle, Lock, Zap } from 'lucide-react';
import { useParadoxStore } from '../../features/games/stores/paradoxStore';

const PANEL = 'rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]';
const SHU_CTA =
  'inline-flex items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-6 py-4 font-manga text-base font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] cursor-pointer';
const GHOST_BTN =
  'inline-flex items-center justify-center gap-2 rounded-xl border border-[#F4F1E8]/15 px-6 py-4 font-black uppercase tracking-widest text-sm text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] cursor-pointer';

const ParadoxGamePage: React.FC = () => {
  const { t } = useTranslation();
  const { gameState, isLoading, error, errorKind, loadGame, submitGuess } = useParadoxStore();

  useEffect(() => {
    loadGame();
  }, [loadGame]);

  if (isLoading)
    return (
      <div className="min-h-screen bg-[#0B0C10] text-center py-20 text-[#F4F1E8] font-black animate-pulse uppercase tracking-[0.3em]">
        {t('games.paradox.loading', "Ouverture d'une faille temporelle...")}
      </div>
    );

  if (error && errorKind === 'auth') {
    return (
      <div className="min-h-screen bg-[#0B0C10] flex justify-center items-center py-20 px-6">
        <div className={`${PANEL} border-[#FDB913]/40 text-center p-8 md:p-10 max-w-md`}>
          <Lock className="w-16 h-16 text-[#FDB913] mx-auto mb-6" />
          <h2 className="font-manga text-2xl font-black italic uppercase text-[#F4F1E8] mb-4">
            {t('games.paradox.auth_required', 'CONNEXION REQUISE')}
          </h2>
          <p className="mb-8 font-bold text-[#8F94A5]">{error}</p>
          <Link to="/auth/login/" className={`${SHU_CTA} mx-auto`}>
            {t('games.paradox.login', 'Se connecter')}
          </Link>
        </div>
      </div>
    );
  }

  if (error && errorKind === 'payment') {
    return (
      <div className="min-h-screen bg-[#0B0C10] flex justify-center items-center py-20 px-6">
        <div className={`${PANEL} border-[#FDB913]/40 text-center p-8 md:p-10 max-w-md`}>
          <Zap className="w-16 h-16 text-[#FDB913] mx-auto mb-6" />
          <h2 className="font-manga text-2xl font-black italic uppercase text-[#F4F1E8] mb-4">
            {t('games.paradox.insufficient_berrix', 'BERRIX INSUFFISANTS')}
          </h2>
          <p className="mb-8 font-bold text-[#8F94A5]">{error}</p>
          <div className="flex gap-3 justify-center">
            <Link to="/power-station/" className={`${SHU_CTA} mx-auto`}>
              {t('games.paradox.recharge_berrix', 'Recharger des Berrix')}
            </Link>
            <button className={GHOST_BTN} onClick={loadGame}>
              {t('common.retry', 'Réessayer')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0B0C10] flex justify-center items-center py-20 px-6">
        <div className={`${PANEL} border-[#E8442B]/40 text-center p-8 md:p-10 max-w-md`}>
          <AlertTriangle className="w-16 h-16 text-[#E8442B] mx-auto mb-6" />
          <h2 className="font-manga text-2xl font-black italic uppercase text-[#E8442B] mb-4">
            {t('games.paradox.unstable_title', 'PARADOXE INSTABLE')}
          </h2>
          <p className="mb-8 font-bold text-[#8F94A5]">{error}</p>
          <button className={SHU_CTA} onClick={loadGame}>
            {t('games.paradox.reset_flux', 'RÉINITIALISER LE FLUX')}
          </button>
        </div>
      </div>
    );
  }

  if (!gameState) return null;

  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <h1 className="font-manga text-5xl font-black italic uppercase mb-4 text-center tracking-tighter flex items-center justify-center gap-3 text-[#F4F1E8]">
          <span className="explore-stamp -rotate-2" aria-hidden>
            逆
          </span>
          PARADOX <span className="text-[#E8442B]">INTRUDER</span>
        </h1>
        <p className="text-center text-[#8F94A5] font-bold uppercase tracking-widest mb-12">
          {t('games.paradox.subtitle', "Démasquez l'anomalie sémantique")}
        </p>

        {gameState.gameOver ? (
          <div className="max-w-2xl mx-auto text-center">
            <div className={`${PANEL} border-[#FDB913]/40 p-8 md:p-10`}>
              <Trophy className="w-20 h-20 text-[#FDB913] mx-auto mb-6 animate-bounce" />
              <h2 className="font-manga text-4xl font-black italic uppercase mb-4 text-[#F4F1E8]">
                {t('games.paradox.solved_title', 'ANOMALIE RÉSOLUE !')}
              </h2>
              <p className="text-xl mb-8 text-[#8F94A5]">
                {t(
                  'games.paradox.solved_desc',
                  "Vous avez démasqué l'intrus avec une précision chirurgicale.",
                )}
              </p>
              <button className={`${SHU_CTA} mx-auto`} onClick={loadGame}>
                <RotateCcw className="w-5 h-5" /> {t('games.paradox.replay', 'REJOUER')}
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {gameState.items.map((item) => (
              <div
                key={item.id}
                onClick={() => submitGuess(item.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    submitGuess(item.id);
                  }
                }}
                role="button"
                tabIndex={0}
                aria-label={t('games.paradox.select_item', {
                  defaultValue: 'Sélectionner {{title}}',
                  title: item.title,
                })}
                className="group relative bg-[#0F1016] rounded-2xl overflow-hidden shadow-xl cursor-pointer transition-all hover:scale-[1.03] border border-[#F4F1E8]/10 hover:border-[#E8442B]/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
              >
                <img
                  src={item.image}
                  className="w-full h-80 object-cover grayscale group-hover:grayscale-0 transition-all duration-700"
                  alt={item.title}
                  loading="lazy"
                  decoding="async"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity"></div>
                <div className="absolute bottom-6 left-6 right-6 text-center">
                  <h3 className="font-manga text-white font-black italic uppercase text-xl leading-none mb-2">
                    {item.title}
                  </h3>
                  <div className="flex items-center justify-center gap-2 text-[#E8442B] opacity-0 group-hover:opacity-100 transition-opacity">
                    <Target className="w-4 h-4" />
                    <span className="text-[10px] font-black uppercase">
                      {t('games.paradox.eliminate', "ÉLIMINER L'ANOMALIE")}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ParadoxGamePage;

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { HelpCircle, Plus, LogIn, ArrowRight, Eye, Swords, Search } from 'lucide-react';

const CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const newCode = () =>
  Array.from({ length: 5 }, () => CHARS[Math.floor(Math.random() * CHARS.length)]).join('');
const panel = 'rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]';

const QuizWhoDuelLobbyPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [joinCode, setJoinCode] = useState('');
  const enter = (code: string) => {
    const c = code.trim().toUpperCase();
    if (c) navigate(`/game/quiz-who/arena/${c}/`);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <header className="relative mb-8">
        <div
          className="explore-halftone pointer-events-none absolute -inset-x-6 -top-8 h-40"
          aria-hidden
        />
        <div className="relative flex items-center gap-3">
          <span className="explore-stamp -rotate-2" aria-hidden>
            誰
          </span>
          <span className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
            <Search className="w-4 h-4" /> {t('games.quiz_who.kicker', 'Qui est-ce ? · Duel')}
          </span>
        </div>
        <h1 className="font-manga relative mt-4 text-5xl sm:text-6xl font-black italic uppercase tracking-tighter text-[#F4F1E8] leading-none">
          {t('games.quiz_who.title', 'Qui est-ce ?')}
        </h1>
        <p className="relative mt-3 max-w-2xl text-sm font-bold uppercase tracking-widest text-[#8F94A5]">
          {t(
            'games.quiz_who.subtitle',
            "Chacun son perso secret — démasquez l'adversaire en premier",
          )}
        </p>
        <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
      </header>

      <div className="grid md:grid-cols-2 gap-6">
        <div className={`${panel} p-6 space-y-5`}>
          <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-[#8F94A5] flex items-center gap-2">
            <Plus className="w-4 h-4" /> {t('games.quiz_who.create_duel', 'Créer un duel')}
          </h3>
          <p className="text-[11px] text-[#8F94A5]/80 italic">
            {t(
              'games.quiz_who.create_desc',
              'Génère un salon et partage le code avec ton adversaire (2 joueurs).',
            )}
          </p>
          <button
            onClick={() => enter(newCode())}
            className="w-full py-4 rounded-xl bg-[#E8442B] hover:bg-[#c93a24] text-[#F4F1E8] font-manga font-black italic uppercase tracking-widest text-lg transition-colors flex items-center justify-center gap-2 border-none cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
          >
            <Plus className="w-5 h-5" /> {t('games.quiz_who.create_btn', 'Créer le duel')}
          </button>
        </div>

        <div className={`${panel} p-6 space-y-5`}>
          <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-[#8F94A5] flex items-center gap-2">
            <LogIn className="w-4 h-4" /> {t('games.quiz_who.join_duel', 'Rejoindre un duel')}
          </h3>
          <p className="text-[11px] text-[#8F94A5]/80 italic">
            {t('games.quiz_who.join_desc', 'Saisis le code du salon partagé.')}
          </p>
          <input
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value.toUpperCase().slice(0, 8))}
            onKeyDown={(e) => {
              if (e.key === 'Enter') enter(joinCode);
            }}
            placeholder={t('games.quiz_who.code_placeholder', 'CODE…')}
            aria-label={t('games.quiz_who.code_aria', 'Code du salon')}
            className="w-full p-3.5 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none transition-colors font-black tracking-[0.3em] text-2xl text-center text-[#F4F1E8] placeholder:text-[#8F94A5]/40 font-mono uppercase"
          />
          <button
            onClick={() => enter(joinCode)}
            disabled={!joinCode.trim()}
            className="w-full py-4 rounded-xl border border-[#F4F1E8]/15 enabled:hover:border-[#FDB913] enabled:hover:text-[#F4F1E8] text-[#8F94A5] font-manga font-black italic uppercase tracking-widest text-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 bg-transparent cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
          >
            <ArrowRight className="w-5 h-5" /> {t('games.quiz_who.join_btn', 'Rejoindre')}
          </button>
        </div>
      </div>

      <div className={`${panel} p-6 mt-6`}>
        <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-[#8F94A5] mb-4 flex items-center gap-2">
          <HelpCircle className="w-4 h-4" /> {t('games.quiz_who.how_to_play', 'Comment jouer')}
        </h3>
        <div className="grid sm:grid-cols-3 gap-4 text-sm">
          <div className="flex items-start gap-3">
            <Eye className="w-5 h-5 text-[#E8442B] shrink-0 mt-0.5" />
            <p className="text-[#F4F1E8]/80">
              {t('games.quiz_who.how1_1', 'Chacun reçoit un')}{' '}
              <b className="text-[#F4F1E8]">{t('games.quiz_who.how1_b', 'perso secret')}</b>{' '}
              {t('games.quiz_who.how1_2', 'sur un plateau commun.')}
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Search className="w-5 h-5 text-[#E8442B] shrink-0 mt-0.5" />
            <p className="text-[#F4F1E8]/80">
              {t('games.quiz_who.how2_1', 'À ton tour, pose une')}{' '}
              <b className="text-[#F4F1E8]">{t('games.quiz_who.how2_b', 'question oui/non')}</b>{' '}
              {t('games.quiz_who.how2_2', 'et élimine les portraits.')}
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Swords className="w-5 h-5 text-[#E8442B] shrink-0 mt-0.5" />
            <p className="text-[#F4F1E8]/80">
              {t('games.quiz_who.how3_1', "Devine le perso de l'adversaire")}{' '}
              <b className="text-[#F4F1E8]">{t('games.quiz_who.how3_b', 'avant lui')}</b>{' '}
              {t('games.quiz_who.how3_2', 'pour gagner !')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuizWhoDuelLobbyPage;

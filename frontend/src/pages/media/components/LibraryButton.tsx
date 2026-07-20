import React from 'react';
import { Link } from 'react-router-dom';
import { Bookmark } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../../utils/apiClient';
import { useAuthStore } from '../../../store/authStore';

const BTN_CLASS =
  'inline-flex items-center gap-2 px-5 py-2.5 bg-white/10 text-white rounded-lg font-black uppercase italic text-sm border-none cursor-pointer';

export const LibraryButton: React.FC<{ mediaId: string }> = ({ mediaId }) => {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuthStore();
  const queryClient = useQueryClient();
  const [showLogin, setShowLogin] = React.useState(false);

  const favUrl = `/api/v1/media/Manga/${mediaId}/favorite/`;
  const { data } = useQuery<{ is_favorite: boolean; status: string | null }>({
    queryKey: ['manga-favorite', mediaId],
    queryFn: () => apiClient(favUrl),
    enabled: isAuthenticated,
  });

  const mutation = useMutation({
    mutationFn: () =>
      apiClient(favUrl, {
        method: 'POST',
        body: JSON.stringify({ status: 'plan_to_read' }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['manga-favorite', mediaId] }),
  });

  const inLibrary = data?.is_favorite ?? false;

  const onClick = () => {
    if (!isAuthenticated) {
      setShowLogin(true);
      return;
    }
    mutation.mutate();
  };

  return (
    <span className="inline-flex items-center gap-3">
      <button onClick={onClick} className={BTN_CLASS} aria-pressed={inLibrary}>
        <Bookmark className="w-5 h-5" fill={inLibrary ? 'currentColor' : 'none'} />{' '}
        {t('media.detail.library', 'Bibliothèque')}
      </button>
      {showLogin && (
        <Link
          to="/auth/login/"
          className="text-[10px] font-black uppercase tracking-widest text-yellow-400 no-underline"
        >
          {t('media.detail.login_required', 'Connexion requise')}
        </Link>
      )}
    </span>
  );
};

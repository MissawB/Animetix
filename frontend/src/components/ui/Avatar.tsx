import React from 'react';

interface AvatarProps {
  /** URL de la photo de profil ; si absente/en erreur, on retombe sur l'initiale. */
  src?: string | null;
  /** Nom utilisé pour l'initiale de repli et l'attribut alt. */
  name: string;
  /** Taille + forme + éventuel ring — appliqué dans les deux cas (image ou initiale). */
  className?: string;
  /** Couleurs de l'initiale de repli (fond + texte). */
  fallbackClassName?: string;
}

/**
 * Photo de profil avec repli sur l'initiale. Une seule source de vérité pour
 * afficher un avatar de façon cohérente (leaderboard, sidebar, profil…).
 */
export const Avatar: React.FC<AvatarProps> = ({
  src,
  name,
  className = '',
  fallbackClassName = '',
}) => {
  const [ok, setOk] = React.useState(true);
  const initial = (name?.[0] ?? '?').toUpperCase();

  if (src && ok) {
    return (
      // onError assure le repli sur l'initiale si l'image casse (404, lien mort).
      // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
      <img
        src={src}
        alt={name}
        loading="lazy"
        decoding="async"
        onError={() => setOk(false)}
        className={`object-cover ${className}`}
      />
    );
  }

  return (
    <span
      className={`flex items-center justify-center ${className} ${fallbackClassName}`}
      aria-hidden
    >
      {initial}
    </span>
  );
};

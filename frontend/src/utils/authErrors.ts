import type { TFunction } from 'i18next';

/**
 * Turns a Firebase Auth error into something a person can act on.
 *
 * The auth pages used to render `error.message` straight from the SDK, so a
 * mistyped password produced "Firebase: Error (auth/invalid-credential)." — a
 * string that names our vendor, leaks an internal code and tells the user
 * nothing about what to do next.
 *
 * Rules followed here: say what happened and how to fix it, never apologise,
 * never blame, and never reveal whether an email is registered (that is exactly
 * why Firebase collapses wrong-password and unknown-user into one code).
 */

interface FirebaseAuthError {
  code?: string;
  message?: string;
}

const codeOf = (err: unknown): string => {
  const code = (err as FirebaseAuthError)?.code;
  if (typeof code === 'string') return code;
  // Some SDK paths only carry the code inside the message.
  const message = (err as FirebaseAuthError)?.message ?? '';
  const match = /\(auth\/[a-z-]+\)/.exec(message);
  return match ? match[0].slice(1, -1) : '';
};

/** Codes where the user deliberately backed out. Telling them "it failed" would
 *  be scolding them for a decision they made on purpose. */
const CANCELLED = new Set([
  'auth/popup-closed-by-user',
  'auth/cancelled-popup-request',
  'auth/user-cancelled',
]);

const MESSAGES: Record<string, { key: string; fallback: string }> = {
  // Wrong password and unknown account share one message on purpose: telling the
  // two apart would let anyone probe which addresses have an account here.
  'auth/invalid-credential': {
    key: 'auth.error.invalid_credential',
    fallback: 'Email ou mot de passe incorrect. Vérifiez vos identifiants et réessayez.',
  },
  'auth/wrong-password': {
    key: 'auth.error.invalid_credential',
    fallback: 'Email ou mot de passe incorrect. Vérifiez vos identifiants et réessayez.',
  },
  'auth/user-not-found': {
    key: 'auth.error.invalid_credential',
    fallback: 'Email ou mot de passe incorrect. Vérifiez vos identifiants et réessayez.',
  },
  'auth/invalid-email': {
    key: 'auth.error.invalid_email',
    fallback: "Cette adresse email n'est pas valide. Exemple : kenji@animetix.com",
  },
  'auth/missing-password': {
    key: 'auth.error.missing_password',
    fallback: 'Saisissez votre mot de passe.',
  },
  'auth/email-already-in-use': {
    key: 'auth.error.email_in_use',
    fallback:
      'Un compte existe déjà avec cette adresse. Connectez-vous, ou inscrivez-vous avec une autre adresse.',
  },
  'auth/weak-password': {
    key: 'auth.error.weak_password',
    fallback: 'Mot de passe trop court : il en faut au moins 6 caractères.',
  },
  'auth/too-many-requests': {
    key: 'auth.error.too_many_requests',
    fallback: 'Trop de tentatives. Patientez quelques minutes avant de réessayer.',
  },
  'auth/network-request-failed': {
    key: 'auth.error.network',
    fallback: 'Serveur injoignable. Vérifiez votre connexion internet, puis réessayez.',
  },
  'auth/popup-blocked': {
    key: 'auth.error.popup_blocked',
    fallback:
      'Votre navigateur a bloqué la fenêtre Google. Autorisez les pop-ups pour ce site, puis réessayez.',
  },
  'auth/account-exists-with-different-credential': {
    key: 'auth.error.other_provider',
    fallback:
      'Cette adresse est déjà liée à une autre méthode de connexion. Utilisez celle avec laquelle vous avez créé le compte.',
  },
  'auth/user-disabled': {
    key: 'auth.error.user_disabled',
    fallback: 'Ce compte est désactivé. Contactez-nous pour le réactiver.',
  },
  'auth/operation-not-allowed': {
    key: 'auth.error.operation_not_allowed',
    fallback: "Cette méthode de connexion n'est pas activée pour le moment.",
  },
};

/**
 * @returns the message to show, or `null` when the user cancelled on purpose
 *          (close the popup, hit Escape) — in that case, show nothing.
 */
export const authErrorMessage = (err: unknown, t: TFunction): string | null => {
  const code = codeOf(err);
  if (CANCELLED.has(code)) return null;

  const entry = MESSAGES[code];
  if (entry) return t(entry.key, entry.fallback);

  return t('auth.error.unknown', 'La connexion a échoué. Réessayez dans un instant.');
};

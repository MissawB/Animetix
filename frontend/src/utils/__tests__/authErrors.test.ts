import { describe, it, expect } from 'vitest';
import type { TFunction } from 'i18next';
import { authErrorMessage } from '../authErrors';

// The real t() returns the fallback when the key is absent — mirror that.
const t = ((_key: string, fallback: string) => fallback) as unknown as TFunction;

describe('authErrorMessage', () => {
  it('names the actual problem on a bad email or password', () => {
    const msg = authErrorMessage({ code: 'auth/invalid-credential' }, t);
    expect(msg).toMatch(/email ou mot de passe incorrect/i);
    // The vendor and its internal code must never reach the user.
    expect(msg).not.toMatch(/firebase|auth\//i);
  });

  it('gives wrong-password and unknown-account the SAME message', () => {
    // Telling them apart would let anyone probe which addresses have an account.
    const wrong = authErrorMessage({ code: 'auth/wrong-password' }, t);
    const unknown = authErrorMessage({ code: 'auth/user-not-found' }, t);
    expect(wrong).toBe(unknown);
  });

  it('tells a returning user to sign in when the email is taken', () => {
    const msg = authErrorMessage({ code: 'auth/email-already-in-use' }, t);
    expect(msg).toMatch(/compte existe déjà/i);
    expect(msg).toMatch(/connectez-vous/i); // says what to do next
  });

  it('states the password rule instead of just refusing', () => {
    expect(authErrorMessage({ code: 'auth/weak-password' }, t)).toMatch(/6 caractères/i);
  });

  it('stays silent when the user closes the Google popup themselves', () => {
    // Not a failure: showing an error would scold them for their own choice.
    expect(authErrorMessage({ code: 'auth/popup-closed-by-user' }, t)).toBeNull();
    expect(authErrorMessage({ code: 'auth/cancelled-popup-request' }, t)).toBeNull();
  });

  it('explains a blocked popup and how to unblock it', () => {
    const msg = authErrorMessage({ code: 'auth/popup-blocked' }, t);
    expect(msg).toMatch(/pop-ups/i);
  });

  it('reads the code out of the message when the SDK omits the field', () => {
    const err = new Error('Firebase: Error (auth/too-many-requests).');
    expect(authErrorMessage(err, t)).toMatch(/trop de tentatives/i);
  });

  it('falls back to a plain message on an unknown error', () => {
    const msg = authErrorMessage(new Error('boom'), t);
    expect(msg).toMatch(/la connexion a échoué/i);
    expect(msg).not.toMatch(/boom/);
  });

  it('never returns the raw SDK string', () => {
    for (const code of [
      'auth/invalid-credential',
      'auth/invalid-email',
      'auth/network-request-failed',
      'auth/user-disabled',
      'auth/nonexistent-code',
    ]) {
      const msg = authErrorMessage({ code, message: `Firebase: Error (${code}).` }, t);
      expect(msg).not.toMatch(/firebase/i);
    }
  });
});

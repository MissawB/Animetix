import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpApi from 'i18next-http-backend';

i18n
  .use(HttpApi) // Charge les fichiers JSON depuis /public/locales
  .use(LanguageDetector) // Détecte la langue du navigateur
  .use(initReactI18next) // Liaison avec React
  .init({
    fallbackLng: 'en',
    debug: false,
    interpolation: {
      escapeValue: false, // React gère déjà l'échappement XSS
    },
    backend: {
      loadPath: '/locales/{{lng}}/translation.json',
    },
  });

export default i18n;

import React from 'react';
import { useTranslation } from 'react-i18next';

const Footer: React.FC = () => {
  const { t } = useTranslation();
  return (
    <footer className="p-12 text-center text-gray-500 dark:text-gray-400 bg-[#fffcf0] dark:bg-[#1a1a2e] border-t border-black/5 dark:border-white/5 mt-auto transition-colors duration-500">
      <p className="manga-font text-[10px] tracking-[0.3em] mb-3">
        {t('footer.powered_by', 'Powered by Animetix IA & React 19')}
      </p>
      <p className="text-xs italic text-gray-500 dark:text-gray-400">
        &copy; 2026 Animetix Team. All rights reserved.
      </p>
    </footer>
  );
};

export default React.memo(Footer);

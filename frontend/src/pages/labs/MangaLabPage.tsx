import React, { useState } from 'react';
import { Upload, Wand2, Languages, Image as ImageIcon, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../utils/apiClient';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabEmpty,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_CTA,
} from './components/shared/LabKit';

const MangaLabPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState<boolean>(false);

  const translatedLanguageOptions = React.useMemo(
    () => [
      { value: 'French', label: t('labs.manga.lang_fr', 'Français') },
      { value: 'English', label: t('labs.manga.lang_en', 'English') },
      { value: 'Spanish', label: t('labs.manga.lang_es', 'Español') },
      { value: 'German', label: t('labs.manga.lang_de', 'Deutsch') },
      { value: 'Japanese', label: t('labs.manga.lang_ja', '日本語') },
    ],
    [t],
  );
  const [view, setView] = useState<'original' | 'clean' | 'translated'>('original');

  const [imageFile, setImageFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [cleanedUrl, setCleanedUrl] = useState<string | null>(null);
  const [translatedUrl, setTranslatedUrl] = useState<string | null>(null);
  const [targetLanguage, setTargetLanguage] = useState<string>('French');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setCleanedUrl(null);
      setTranslatedUrl(null);
      setView('original');
    }
  };

  const handleClean = async () => {
    if (!imageFile) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', imageFile);

      const response = await apiClient('/api/v1/labs/manga-lab/clean/', {
        method: 'POST',
        body: formData,
        headers: {},
      });

      if (response && response.status === 'success' && response.image) {
        setCleanedUrl(`data:image/png;base64,${response.image}`);
        setView('clean');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTranslate = async () => {
    if (!imageFile) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', imageFile);
      formData.append('target_lang', targetLanguage);

      const response = await apiClient('/api/v1/labs/manga-lab/translate/', {
        method: 'POST',
        body: formData,
        headers: {},
      });

      if (response && response.status === 'success' && response.image) {
        setTranslatedUrl(`data:image/png;base64,${response.image}`);
        setView('translated');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getActiveImageUrl = () => {
    if (view === 'clean') return cleanedUrl;
    if (view === 'translated') return translatedUrl;
    return previewUrl;
  };

  const VIEWS: Array<{ id: 'original' | 'clean' | 'translated'; label: string; enabled: boolean }> =
    [
      { id: 'original', label: t('labs.manga.original', 'ORIGINAL'), enabled: true },
      { id: 'clean', label: t('labs.manga.clean', 'PROPRE'), enabled: !!cleanedUrl },
      { id: 'translated', label: t('labs.manga.translated', 'TRADUIT'), enabled: !!translatedUrl },
    ];

  return (
    <LabPage>
      <LabHeader
        code="Protocole · Manga"
        title="Atelier"
        accent="des planches"
        lede="Importe une page de manga et le laboratoire nettoie les bulles ou traduit le texte directement dans les cases, sans toucher au dessin."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Outils */}
        <div className="lg:col-span-4">
          <LabPanel title={t('labs.manga.ai_tools', 'Outils IA')}>
            <div className="space-y-6">
              <button
                type="button"
                onClick={() => document.getElementById('upload')?.click()}
                className={LAB_CTA}
              >
                <Upload className="h-5 w-5" aria-hidden="true" />{' '}
                {t('labs.manga.btn_import', 'IMPORTER PAGE')}
              </button>
              <input
                type="file"
                id="upload"
                className="hidden"
                onChange={handleFileChange}
                aria-label={t('labs.manga.import_aria', 'Importer une page de manga')}
              />

              <button
                type="button"
                disabled={!previewUrl || loading}
                onClick={handleClean}
                className="flex w-full cursor-pointer items-center gap-4 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 text-left transition-colors hover:border-[#FDB913] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Wand2 className="h-5 w-5 flex-none text-[#FDB913]" aria-hidden="true" />
                <span>
                  <span className="block text-sm font-bold text-[#F4F1E8]">
                    {t('labs.manga.cleaner_title', 'Bubble Cleaner')}
                  </span>
                  <span className="mt-0.5 block text-[10px] text-[#8F94A5]">
                    {t('labs.manga.cleaner_desc', 'Effacer les bulles de texte')}
                  </span>
                </span>
              </button>

              <div className="space-y-4 border-t border-[#F4F1E8]/10 pt-6">
                <div className="space-y-2">
                  <label htmlFor="target-lang" className={LAB_LABEL}>
                    {t('labs.manga.target_language', 'Langue de Traduction')}
                  </label>
                  <select
                    id="target-lang"
                    value={targetLanguage}
                    onChange={(e) => setTargetLanguage(e.target.value)}
                    className={`${LAB_INPUT} cursor-pointer`}
                  >
                    {translatedLanguageOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="button"
                  disabled={!previewUrl || loading}
                  onClick={handleTranslate}
                  className="flex w-full cursor-pointer items-center gap-4 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 text-left transition-colors hover:border-[#FDB913] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Languages className="h-5 w-5 flex-none text-[#FDB913]" aria-hidden="true" />
                  <span>
                    <span className="block text-sm font-bold text-[#F4F1E8]">
                      {t('labs.manga.translator_title', 'Auto-Translator')}
                    </span>
                    <span className="mt-0.5 block text-[10px] text-[#8F94A5]">
                      {t('labs.manga.translator_desc', 'Traduire la planche')}
                    </span>
                  </span>
                </button>
              </div>
            </div>
          </LabPanel>
        </div>

        {/* Visionneuse */}
        <div className="lg:col-span-8">
          {!previewUrl && !loading ? (
            <LabEmpty
              icon={<ImageIcon className="h-20 w-20" aria-hidden="true" />}
              title={t('labs.manga.no_page', 'Aucune page importée')}
              hint="Importe une planche depuis le panneau d'outils : les versions propre et traduite s'afficheront ici."
            />
          ) : (
            <section className="relative flex min-h-[600px] flex-col justify-center overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8">
              {loading && (
                <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-[#0B0C10]/90">
                  <Loader2
                    className="mb-6 h-12 w-12 animate-spin text-[#FDB913]"
                    aria-hidden="true"
                  />
                  <span className="text-xs font-black uppercase tracking-[0.3em] text-[#8F94A5]">
                    {t('common.loading')}
                  </span>
                </div>
              )}
              {previewUrl && (
                <div className="flex min-h-[540px] flex-col justify-between">
                  <div className="mb-8 flex flex-wrap justify-center gap-3">
                    {VIEWS.map((v) => (
                      <button
                        key={v.id}
                        type="button"
                        onClick={() => setView(v.id)}
                        disabled={!v.enabled}
                        className={`cursor-pointer rounded-full border px-5 py-2.5 text-xs font-black uppercase tracking-widest transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                          view === v.id
                            ? 'border-[#FDB913] bg-[#FDB913]/10 text-[#F4F1E8]'
                            : 'border-[#F4F1E8]/15 bg-transparent text-[#8F94A5] hover:border-[#F4F1E8]/30 hover:text-[#F4F1E8]'
                        }`}
                      >
                        {v.label}
                      </button>
                    ))}
                  </div>
                  <div className="flex flex-grow items-center justify-center">
                    <img
                      src={getActiveImageUrl() || ''}
                      className="mx-auto max-h-[700px] rounded-xl object-contain"
                      alt="Manga Page View"
                      loading="lazy"
                      decoding="async"
                    />
                  </div>
                </div>
              )}
            </section>
          )}
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Importe une planche',
            body: t(
              'labs.manga.guide_concept_desc',
              "Importez une page de manga et laissez l'IA la nettoyer ou la traduire, sans toucher au dessin.",
            ),
          },
          {
            title: 'Nettoie les bulles',
            body: t(
              'labs.manga.guide_cleaner_desc',
              'Efface le texte des bulles pour obtenir une planche vierge, prête à recevoir votre propre texte ou une nouvelle traduction.',
            ),
          },
          {
            title: 'Traduis la page',
            body: t(
              'labs.manga.guide_translator_desc',
              'Choisissez une langue cible et la planche est traduite directement dans les bulles. Comparez les versions avec les onglets Original, Propre et Traduit.',
            ),
          },
        ]}
        note={`${t('labs.manga.guide_footer_1', 'La page est envoyée au backend qui détecte les bulles de texte, en extrait le contenu par OCR, puis efface le lettrage par inpainting pour produire la version "propre".')} ${t('labs.manga.guide_footer_2', "Pour la traduction, le texte reconnu est traduit dans la langue cible puis réinséré dans les bulles, et l'image finale est renvoyée encodée en base64.")}`}
      />
    </LabPage>
  );
};

export default MangaLabPage;

import React, { useState } from 'react';
import { Upload, Wand2, Languages, Image as ImageIcon, Sparkles } from 'lucide-react';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Select } from "../../components/ui/Select";
import { useTranslation } from 'react-i18next';
import { apiClient } from "../../utils/apiClient";

const LANGUAGE_OPTIONS = [
  { value: 'French', label: 'Français' },
  { value: 'English', label: 'English' },
  { value: 'Spanish', label: 'Español' },
  { value: 'German', label: 'Deutsch' },
  { value: 'Japanese', label: '日本語' },
];

const MangaLabPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState<boolean>(false);
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
        headers: {} 
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
        headers: {} 
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

  return (
    <div className="container mx-auto py-12 px-6">
      <h1 className="text-6xl font-black italic manga-font mb-12 tracking-tighter uppercase text-center md:text-left">
          MANGA <span className="text-yellow-400">LAB</span>
      </h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
        <Card padding="lg" className="lg:col-span-1 h-fit space-y-6">
          <Button 
            variant="primary" 
            fullWidth 
            className="bg-yellow-400 text-black hover:bg-yellow-500 border-none" 
            onClick={() => document.getElementById('upload')?.click()}
          >
            <Upload className="w-5 h-5" /> IMPORTER PAGE
          </Button>
          <input type="file" id="upload" className="hidden" onChange={handleFileChange} aria-label="Importer une page de manga" />
          
          <div className="space-y-4">
              <h4 className="text-[10px] font-black uppercase opacity-30 tracking-widest">Outils IA</h4>
              
              <button 
                disabled={!previewUrl || loading}
                onClick={handleClean}
                className="w-full p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl flex items-center gap-4 cursor-pointer hover:bg-yellow-400/10 transition-colors disabled:opacity-30 border border-transparent hover:border-yellow-400/20"
              >
                  <Wand2 className="w-5 h-5 text-yellow-500" />
                  <div className="text-left">
                    <span className="font-bold text-sm block">Bubble Cleaner</span>
                    <span className="text-[10px] text-white/40 block mt-0.5">Effacer les bulles de texte</span>
                  </div>
              </button>

              <div className="border-t border-white/5 pt-4 space-y-3">
                <Select
                  id="target-lang"
                  label="Langue de Traduction"
                  value={targetLanguage}
                  onChange={(val) => setTargetLanguage(val)}
                  options={LANGUAGE_OPTIONS}
                />
                
                <button 
                  disabled={!previewUrl || loading}
                  onClick={handleTranslate}
                  className="w-full p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl flex items-center gap-4 cursor-pointer hover:bg-blue-400/10 transition-colors disabled:opacity-30 border border-transparent hover:border-blue-400/20"
                >
                    <Languages className="w-5 h-5 text-blue-500" />
                    <div className="text-left">
                      <span className="font-bold text-sm block">Auto-Translator</span>
                      <span className="text-[10px] text-white/40 block mt-0.5">Traduire la planche</span>
                    </div>
                </button>
              </div>
          </div>
        </Card>

        <div className="lg:col-span-3 bg-black rounded-[3rem] shadow-2xl min-h-[600px] relative overflow-hidden border-4 border-white/5 flex flex-col justify-center">
          {loading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 backdrop-blur-sm z-50">
                <div className="w-20 h-20 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mb-6"></div>
                <span className="text-white font-black italic uppercase tracking-[0.3em]">{t('common.loading')}</span>
            </div>
          ) : previewUrl ? (
            <div className="flex flex-col h-full p-8 justify-between min-h-[600px]">
              <div className="flex gap-4 mb-8 justify-center">
                <Button 
                    onClick={() => setView('original')} 
                    variant={view === 'original' ? 'primary' : 'outline'}
                    className={view === 'original' ? 'bg-yellow-400 text-black border-none' : ''}
                >
                    ORIGINAL
                </Button>
                <Button 
                    onClick={() => setView('clean')} 
                    disabled={!cleanedUrl}
                    variant={view === 'clean' ? 'primary' : 'outline'}
                    className={view === 'clean' ? 'bg-emerald-500 text-white border-none' : ''}
                >
                    PROPRE
                </Button>
                <Button 
                    onClick={() => setView('translated')} 
                    disabled={!translatedUrl}
                    variant={view === 'translated' ? 'primary' : 'outline'}
                    className={view === 'translated' ? 'bg-blue-500 text-white border-none' : ''}
                >
                    TRADUIT
                </Button>
              </div>
              <div className="relative group cursor-zoom-in flex-grow flex items-center justify-center">
                  <img 
                    src={getActiveImageUrl() || ''} 
                    className="rounded-2xl mx-auto max-h-[700px] shadow-2xl transition-transform duration-500 group-hover:scale-[1.01] object-contain" 
                    alt="Manga Page View" 
                    loading="lazy"
                    decoding="async"
                  />
              </div>
            </div>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center opacity-20">
                <ImageIcon className="w-32 h-32 text-white mb-6" />
                <span className="text-white font-black italic text-xl uppercase tracking-widest">Aucune page importée</span>
            </div>
          )}
        </div>
      </div>

      {/* Guide & Protocole */}
      <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
          <Card padding="lg" className="bg-white dark:bg-black/40 border-amber-500/20 shadow-[0_0_50px_rgba(245,158,11,0.1)] relative overflow-hidden group">
              <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                  <ImageIcon className="w-64 h-64 text-amber-500" />
              </div>
              <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                  <Sparkles className="w-5 h-5 text-amber-600 dark:text-amber-400" /> Guide du Manga Lab
              </h4>
              <div className="space-y-4 relative z-10">
                  <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                      <span className="text-amber-600 dark:text-amber-400">Le Concept :</span> Importez une page de manga et laissez l'IA la nettoyer ou la traduire, sans toucher au dessin.
                  </p>
                  <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                      <span className="text-amber-600 dark:text-amber-400">Bubble Cleaner :</span> Efface le texte des bulles pour obtenir une planche vierge, prête à recevoir votre propre texte ou une nouvelle traduction.
                  </p>
                  <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                      <span className="text-amber-600 dark:text-amber-400">Auto-Translator :</span> Choisissez une langue cible et la planche est traduite directement dans les bulles. Comparez les versions avec les onglets Original, Propre et Traduit.
                  </p>
              </div>
          </Card>

          <div className="p-12 rounded-[4rem] bg-gradient-to-br from-amber-600/10 to-transparent border border-black/5 dark:border-white/5 flex flex-col justify-center text-center">
              <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-amber-800/70 dark:text-amber-200/60">
                  La page est envoyée au backend qui détecte les bulles de texte, en extrait le contenu par OCR, puis efface le lettrage par inpainting pour produire la version "propre". <br />
                  Pour la traduction, le texte reconnu est traduit dans la langue cible puis réinséré dans les bulles, et l'image finale est renvoyée encodée en base64.
              </p>
          </div>
      </div>
    </div>
  );
};

export default MangaLabPage;

import React, { useState } from 'react';
import { Upload, Wand2, Languages, Image as ImageIcon } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../../utils/apiClient';

interface MangaLabResult {
  original: string;
  cleaned: string;
  translated: string;
  title?: string;
}

const MangaLabPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<MangaLabResult | null>(null);
  const [view, setView] = useState<'clean' | 'translated'>('clean');

  const [imageFile, setImageFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleProcess = async (action: 'clean' | 'translate') => {
    if (!imageFile && !previewUrl) return;
    setLoading(true);
    try {
      const formData = new FormData();
      if (imageFile) formData.append('image_file', imageFile);
      else if (previewUrl) formData.append('image_url', previewUrl);
      
      formData.append('action', action);
      formData.append('language', 'Français');

      const data = await apiClient('/api/v1/manga-lab/', {
        method: 'POST',
        body: formData,
        // Headers automatiques via apiClient, mais FormData nécessite de NE PAS mettre Content-Type
        headers: {} 
      });
      
      setResult(data);
      setView(action === 'translate' ? 'translated' : 'clean');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-12 px-6">
      <h1 className="text-6xl font-black italic manga-font mb-12 tracking-tighter uppercase text-center md:text-left">
          MANGA <span className="text-yellow-400">LAB</span>
      </h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
        <Card padding="lg" className="lg:col-span-1 h-fit">
          <Button 
            variant="primary" 
            fullWidth 
            className="bg-yellow-400 text-black hover:bg-yellow-500 border-none" 
            onClick={() => document.getElementById('upload')?.click()}
          >
            <Upload className="w-5 h-5" /> IMPORTER PAGE
          </Button>
          <input type="file" id="upload" className="hidden" onChange={handleFileChange} />
          
          <div className="mt-8 space-y-4">
              <h4 className="text-[10px] font-black uppercase opacity-30 tracking-widest">Outils IA</h4>
              <button 
                disabled={!previewUrl || loading}
                onClick={() => handleProcess('clean')}
                className="w-full p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl flex items-center gap-4 cursor-pointer hover:bg-yellow-400/10 transition-colors disabled:opacity-30 border border-transparent hover:border-yellow-400/20"
              >
                  <Wand2 className="w-5 h-5 text-yellow-500" />
                  <span className="font-bold text-sm text-left">Bubble Cleaner</span>
              </button>
              <button 
                disabled={!previewUrl || loading}
                onClick={() => handleProcess('translate')}
                className="w-full p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl flex items-center gap-4 cursor-pointer hover:bg-blue-400/10 transition-colors disabled:opacity-30 border border-transparent hover:border-blue-400/20"
              >
                  <Languages className="w-5 h-5 text-blue-500" />
                  <span className="font-bold text-sm text-left">Auto-Translator</span>
              </button>
          </div>
        </Card>

        <div className="lg:col-span-3 bg-black rounded-[3rem] shadow-2xl min-h-[600px] relative overflow-hidden border-4 border-white/5">
          {loading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 backdrop-blur-sm z-50">
                <div className="w-20 h-20 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mb-6"></div>
                <span className="text-white font-black italic uppercase tracking-[0.3em]">{t('common.loading')}</span>
            </div>
          ) : result ? (
            <div className="flex flex-col h-full p-8">
              <div className="flex gap-4 mb-8 justify-center">
                <Button 
                    onClick={() => setView('clean')} 
                    variant={view === 'clean' ? 'primary' : 'outline'}
                    className={view === 'clean' ? 'bg-yellow-400 text-black border-none' : ''}
                >
                    CLEAN
                </Button>
                <Button 
                    onClick={() => setView('translated')} 
                    variant={view === 'translated' ? 'primary' : 'outline'}
                    className={view === 'translated' ? 'bg-blue-500 border-none' : ''}
                >
                    TRADUIT
                </Button>
              </div>
              <div className="relative group cursor-zoom-in">
                  <img src={view === 'clean' ? result.cleaned : result.translated} className="rounded-2xl mx-auto max-h-[700px] shadow-2xl transition-transform duration-500 group-hover:scale-[1.02]" alt="Résultat" />
              </div>
            </div>
          ) : previewUrl ? (
            <div className="flex items-center justify-center h-full p-8">
                <img src={previewUrl} className="rounded-2xl max-h-[700px] opacity-50 grayscale" alt="Preview" />
                <div className="absolute inset-0 flex items-center justify-center">
                    <Badge variant="neutral" className="bg-black/60 backdrop-blur-md border-white/20 py-3 px-6 text-sm">
                        Page chargée • Sélectionnez un outil
                    </Badge>
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
    </div>
  );
};

export default MangaLabPage;


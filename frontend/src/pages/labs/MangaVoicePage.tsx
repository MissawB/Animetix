import React, { useState } from 'react';
import { Mic, Play, Save, User, MessageSquare, Wand2 } from 'lucide-react';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { apiClient } from "../../utils/apiClient";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

const MangaVoicePage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [text, setText] = useState<string>('');
  const [character, setCharacter] = useState<string>('Naruto');
  const [refAudio, setRefAudio] = useState<File | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const CHARACTERS = [
    { id: 'Naruto', name: 'Naruto Uzumaki', color: 'bg-orange-500' },
    { id: 'Sasuke', name: 'Sasuke Uchiha', color: 'bg-purple-600' },
    { id: 'Goku', name: 'Son Goku', color: 'bg-red-500' },
    { id: 'Luffy', name: 'Monkey D. Luffy', color: 'bg-red-600' },
    { id: 'Rem', name: 'Rem (Re:Zero)', color: 'bg-blue-400' },
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setRefAudio(file);
    }
  };

  const handleGenerate = async () => {
    if (!text || !refAudio) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('text', text);
      formData.append('character', character);
      formData.append('reference_audio', refAudio);

      const data = await apiClient('/api/v1/labs/manga-voice/', {
        method: 'POST',
        body: formData,
        headers: {} 
      });
      
      setAudioUrl(data.audio_data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatedPage>
      <div className="container mx-auto py-12 px-6">
        <header className="mb-16 text-center md:text-left">
            <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase mb-4">
                MANGA <span className="text-orange-500 text-glow">VOICE</span> LAB
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Donnez vie à vos planches avec le doublage IA zero-shot et le clonage vocal instantané.
            </p>
        </header>
        
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
          <Card padding="lg" className="lg:col-span-1 h-fit bg-gray-900/40 border-white/5 shadow-2xl">
            <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                <User className="w-4 h-4" /> Casting Personnage
            </h3>

            <div className="space-y-3 mb-8">
                {CHARACTERS.map((c) => (
                    <button
                        key={c.id}
                        onClick={() => setCharacter(c.id)}
                        className={`w-full px-5 py-4 rounded-2xl text-left text-xs font-black transition-all border-2 flex items-center justify-between group ${
                            character === c.id 
                            ? 'border-orange-500 bg-orange-500/10 text-white shadow-lg' 
                            : 'border-white/5 bg-black/20 text-white/40 hover:border-white/10'
                        }`}
                    >
                        <div className="flex items-center gap-3">
                            <div className={`w-3 h-3 rounded-full ${c.color} group-hover:animate-pulse`} />
                            {c.name}
                        </div>
                        {character === c.id && <div className="w-1.5 h-1.5 bg-white rounded-full" />}
                    </button>
                ))}
            </div>

            <div className="pt-6 border-t border-white/5">
                <h4 className="text-[10px] font-black uppercase opacity-30 mb-4 tracking-widest">Audio de Référence</h4>
                <Button 
                    variant="outline" 
                    fullWidth 
                    className="bg-black text-white hover:bg-gray-800 border-none rounded-xl py-4" 
                    onClick={() => document.getElementById('audio-upload')?.click()}
                >
                    <Mic className="w-4 h-4" /> {refAudio ? 'VOIX CHARGÉE' : 'CHARGER UNE VOIX'}
                </Button>
                <input type="file" id="audio-upload" className="hidden" accept="audio/*" onChange={handleFileChange} />
                {refAudio && (
                    <p className="text-[9px] text-center mt-2 opacity-40 font-bold uppercase truncate">{refAudio.name}</p>
                )}
            </div>
          </Card>

          <div className="lg:col-span-3 space-y-8">
            <Card padding="lg" className="bg-black border-2 border-white/5 rounded-[3rem] shadow-2xl">
                <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-orange-500" /> Script du Dialogue
                </h3>
                <textarea 
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Entrez le texte que le personnage doit dire..."
                    className="w-full h-40 bg-gray-900/50 border border-white/5 rounded-2xl p-6 text-lg font-bold text-white outline-none focus:border-orange-500/50 transition-all resize-none placeholder:opacity-20"
                />
                <div className="flex justify-end mt-6">
                    <Button 
                        onClick={handleGenerate}
                        disabled={!text || !refAudio || loading}
                        className="bg-orange-500 hover:bg-orange-400 text-white px-12 py-8 rounded-2xl font-black italic text-xl uppercase shadow-xl shadow-orange-500/20 hover:scale-105 active:scale-95 transition-all"
                    >
                        {loading ? <Wand2 className="w-6 h-6 animate-spin" /> : "GÉNÉRER LE DUBBING"}
                    </Button>
                </div>
            </Card>

            <AnimatePresence>
                {audioUrl && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                    >
                        <Card padding="lg" className="bg-gradient-to-br from-orange-500/20 to-transparent border-orange-500/30 rounded-[3rem] p-10 flex flex-col items-center gap-8 shadow-2xl relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-6">
                                <Badge variant="success" className="bg-orange-500 text-white font-black italic border-none px-4 py-2">RVC v2 OPTIMIZED</Badge>
                            </div>

                            <div className="w-24 h-24 bg-orange-500 rounded-full flex items-center justify-center shadow-2xl shadow-orange-500/50 animate-pulse">
                                <Play className="w-10 h-10 text-white ml-1" />
                            </div>
                            
                            <div className="text-center">
                                <h3 className="text-2xl font-black italic manga-font uppercase mb-2 tracking-tighter">Dubbing Terminé</h3>
                                <p className="text-xs font-bold opacity-50 uppercase tracking-widest">Le personnage de {character} est prêt à parler.</p>
                            </div>

                            <audio controls src={audioUrl} className="w-full max-w-xl accent-orange-500">
                                <track kind="captions" />
                            </audio>
                            
                            <div className="flex gap-4">
                                <Button variant="outline" className="border-white/10 hover:bg-white/5 rounded-xl px-8">
                                    <Save className="w-4 h-4 mr-2" /> SAUVEGARDER
                                </Button>
                                <Button variant="primary" className="bg-white text-black hover:bg-gray-200 border-none rounded-xl px-8 font-black uppercase italic">
                                    INJECTER DANS LA PLANCHE
                                </Button>
                            </div>
                        </Card>
                    </motion.div>
                )}
            </AnimatePresence>
            
            {!audioUrl && !loading && (
                <div className="h-64 border-4 border-dashed border-white/5 rounded-[3rem] flex flex-col items-center justify-center opacity-20">
                    <Mic className="w-16 h-16 mb-4" />
                    <span className="font-black italic uppercase tracking-widest">En attente de génération</span>
                </div>
            )}
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default MangaVoicePage;

import React, { useState } from 'react';

const MangaLabPage = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [view, setView] = useState('clean');

  const processManga = async (url, title) => {
    setLoading(true);
    try {
      const res = await fetch('/manga_lab/clean/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ image_url: url })
      });
      const data = await res.json();
      setResult({ ...data, original: url, title });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-12">
      <h1 className="text-5xl font-black mb-8">MANGA LAB</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1 p-4 bg-gray-100 rounded-2xl">
          <button className="btn btn-warning w-full mb-4" onClick={() => document.getElementById('upload').click()}>
            Importer Page
          </button>
          <input type="file" id="upload" className="hidden" />
          {/* Exemple liste simplifiée */}
        </div>

        <div className="lg:col-span-3 bg-black p-4 rounded-3xl min-h-[600px] relative">
          {loading && <div className="absolute inset-0 flex items-center justify-center text-white font-bold">ANALYSE IA...</div>}
          {result && (
            <div className="flex flex-col h-full">
              <div className="flex gap-2 mb-4 justify-center">
                <button onClick={() => setView('clean')} className={`btn ${view === 'clean' ? 'btn-warning' : 'btn-outline-warning'}`}>Clean</button>
                <button onClick={() => setView('translated')} className={`btn ${view === 'translated' ? 'btn-info' : 'btn-outline-info'}`}>Traduit</button>
              </div>
              <img src={view === 'clean' ? result.cleaned : result.translated} className="rounded-xl mx-auto max-h-[500px]" alt="Résultat" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export default MangaLabPage;

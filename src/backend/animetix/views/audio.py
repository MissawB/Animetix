import os
import base64
import logging
from io import BytesIO
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from ..containers import get_container
from ..session_manager import GameSessionManager
from pydub import AudioSegment

logger = logging.getLogger('animetix')

def audio_lab_view(request):
    """Affiche l'interface de l'Audio Lab."""
    # Liste des voix en bibliothèque (simulée pour le moment)
    library_voices = [
        {"id": "naruto", "name": "Naruto", "icon": "🍥"},
        {"id": "luffy", "name": "Luffy", "icon": "🏴‍☠️"},
        {"id": "goku", "name": "Goku", "icon": "🐉"},
    ]
    return render(request, 'animetix/audio/audio_lab.html', {
        'library_voices': library_voices
    })

@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def clone_voice_api(request):
    """Point de terminaison pour le clonage de voix."""
    container = get_container()
    if request.method != 'POST':
        return redirect('audio_lab')
    
    text = request.POST.get('text', '').strip()
    voice_source = request.POST.get('source_type') # 'library', 'upload', 'mic'
    
    if not text:
        return JsonResponse({'error': 'Texte manquant.'}, status=400)
    
    try:
        ref_audio_bytes = b""
        if voice_source == 'library':
            voice_id = request.POST.get('voice_id')
            # Fallback path for demo
            path = os.path.join("data", "audio", "library", f"{voice_id}.wav")
            if os.path.exists(path):
                with open(path, "rb") as f: ref_audio_bytes = f.read()
        elif voice_source in ['upload', 'mic']:
            audio_file = request.FILES.get('audio_data')
            if audio_file: ref_audio_bytes = audio_file.read()

        if not ref_audio_bytes:
            return JsonResponse({'error': 'Échantillon vocal manquant.'}, status=400)

        # 1. Génération via XTTS (Port d'inférence)
        cloned_wav = container.voice_cloning_service.generate_character_voice(
            text=text, 
            character_audio_sample=ref_audio_bytes
        )

        if not cloned_wav:
            return JsonResponse({'error': 'Échec de la génération IA.'}, status=500)

        # 2. Conversion WAV -> MP3 via pydub
        wav_io = BytesIO(cloned_wav)
        audio = AudioSegment.from_wav(wav_io)
        mp3_io = BytesIO()
        audio.export(mp3_io, format="mp3", bitrate="128k")
        mp3_bytes = mp3_io.getvalue()

        # 3. Envoi au format Base64
        res_b64 = base64.b64encode(mp3_bytes).decode('utf-8')
        return JsonResponse({
            'status': 'success',
            'audio_base64': f"data:audio/mp3;base64,{res_b64}",
            'filename': f"animetix-clone-{os.urandom(4).hex()}.mp3"
        })

    except Exception as e:
        logger.error(f"Audio Lab Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

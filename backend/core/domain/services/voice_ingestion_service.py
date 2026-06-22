import io
import logging
import os
import tempfile
from typing import Any

from core.domain.exceptions import InferenceError
from core.ports.voice_profile_port import VoiceProfileRepositoryPort

logger = logging.getLogger("animetix.voice_ingestion_service")


class VoiceIngestionService:
    """
    Service to ingest voice actors/seiyuu profiles dynamically from YouTube.
    Downloads, slices, filters (bandpass), and saves the sample via the injected
    voice-profile repository port (no direct ORM/file access in the domain).
    """

    def __init__(self, voice_profile_repository: VoiceProfileRepositoryPort):
        self.voice_profile_repository = voice_profile_repository

    def ingest_voice(
        self,
        name: str,
        language: str,
        youtube_url_or_query: str,
        definition: str = "",
        roles: str = "",
        impact: str = "Custom",
    ) -> Any:
        """
        Ingests a voice profile from a YouTube link or query.
        """
        if not name:
            raise ValueError("Le nom du doubleur/seiyuu est requis.")
        if not youtube_url_or_query:
            raise ValueError("L'URL ou la requête de recherche YouTube est requise.")

        logger.info(
            f"Début de l'ingestion de la voix pour '{name}' via source: {youtube_url_or_query}"
        )

        try:
            import yt_dlp
            from pydub import AudioSegment
            from pydub.silence import detect_leading_silence
        except ImportError as e:
            logger.error(f"Erreur d'importation des dépendances d'ingestion : {e}")
            raise InferenceError(
                f"Les dépendances requises (yt-dlp, pydub) ne sont pas installées. Détail: {str(e)}"
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(temp_dir, "%(id)s.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "wav",
                        "preferredquality": "192",
                    }
                ],
            }

            url = youtube_url_or_query
            if url.startswith("http://") or url.startswith("https://"):
                from core.utils.security import is_safe_url

                if not is_safe_url(url):
                    raise InferenceError(
                        "URL source non sécurisée détectée (SSRF bloqué)."
                    )
            else:
                url = f"ytsearch1:{url}"

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if not info:
                        raise InferenceError("Aucune information extraite de YouTube.")

                    if "entries" in info:
                        # Cas d'une recherche, prend la première entrée
                        if not info["entries"]:
                            raise InferenceError(
                                "Aucun résultat trouvé sur YouTube pour cette requête."
                            )
                        video_info = info["entries"][0]
                    else:
                        video_info = info

                    video_id = video_info["id"]
                    webpage_url = video_info.get("webpage_url", youtube_url_or_query)
                    if webpage_url.startswith("http://") or webpage_url.startswith(
                        "https://"
                    ):
                        from core.utils.security import is_safe_url

                        if not is_safe_url(webpage_url):
                            webpage_url = f"https://youtube.com/watch?v={video_id}"

                    wav_path = os.path.join(temp_dir, f"{video_id}.wav")

                    if not os.path.exists(wav_path):
                        raise InferenceError(
                            f"Le fichier WAV n'a pas été généré par yt-dlp : {wav_path}"
                        )

                    # 2. Chargement et Découpage de l'audio via pydub
                    logger.info(f"Chargement de l'audio depuis {wav_path}")
                    sound = AudioSegment.from_file(wav_path)

                    # Détection du silence initial pour caler le début de l'extrait
                    start_trim = detect_leading_silence(sound, silence_threshold=-50.0)
                    duration_ms = 10 * 1000  # 10 secondes

                    if len(sound) - start_trim < 3000:
                        # Si la fin est trop proche du silence détecté, on démarre du début
                        sliced_sound = sound[:duration_ms]
                    else:
                        sliced_sound = sound[start_trim : start_trim + duration_ms]

                    # 3. Filtrage passe-bande simple (humain : ~80Hz à ~8000Hz)
                    logger.info("Application du filtrage passe-bande (80Hz - 8000Hz)")
                    filtered_sound = sliced_sound.high_pass_filter(80).low_pass_filter(
                        8000
                    )

                    # Exportation en bytes WAV
                    out_buffer = io.BytesIO()
                    filtered_sound.export(out_buffer, format="wav")
                    audio_bytes = out_buffer.getvalue()

                    # 4. Enregistrement ou mise à jour du profil (via le port)
                    profile = self.voice_profile_repository.save_voice_sample(
                        name=name,
                        language=language,
                        origin_detail=webpage_url,
                        audio_bytes=audio_bytes,
                        definition=definition,
                        roles=roles,
                        impact=impact,
                    )

                    logger.info(f"Profil vocal '{name}' créé/mis à jour avec succès.")
                    return profile

            except Exception as e:
                logger.error(f"Échec de l'ingestion de la voix : {e}")
                raise InferenceError(f"Erreur lors de l'ingestion YouTube : {str(e)}")

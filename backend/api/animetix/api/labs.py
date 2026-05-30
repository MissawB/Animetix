import os
import json
import datetime
from animetix_project.logging_config import get_logger
from django.conf import settings
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from animetix.api.core import is_safe_url
from ..models import DailyChallenge
from ..serializers import DailyChallengeSerializer
from ..containers import get_container

logger = get_logger('animetix.' + __name__)

class DailyChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyChallenge.objects.all()
    serializer_class = DailyChallengeSerializer
    permission_classes = [permissions.AllowAny]

class LatentSpaceDataView(APIView):
    """Sert les données de projection 3D depuis les artifacts JSON."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        media = request.query_params.get('media', 'anime').lower()
        type_param = request.query_params.get('type', 'thematic').lower()
        
        mapping = {
            ('anime', 'thematic'): 'latent_space_anime_thematic.json',
            ('anime', 'visual'): 'latent_space_anime_visual_vibe.json',
            ('anime', 'scenario'): 'latent_space_anime_plot.json',
            ('manga', 'thematic'): 'latent_space_manga_thematic.json',
            ('manga', 'visual'): 'latent_space_manga_visual_vibe.json',
            ('manga', 'scenario'): 'latent_space_manga_plot.json',
            ('character', 'thematic'): 'latent_space_character_vibe.json',
            ('character', 'visual'): 'latent_space_character_visual_vibe.json',
        }
        
        filename = mapping.get((media, type_param), 'latent_space_3d.json')
        project_root = settings.BASE_DIR.parent.parent
        file_path = project_root / "data" / "artifacts" / filename
        
        if not os.path.exists(file_path):
            file_path = project_root / "data" / "artifacts" / "latent_space_3d.json"
            if not os.path.exists(file_path):
                return Response([], status=status.HTTP_404_NOT_FOUND)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DailyChallengeDataView(APIView):
    """Récupère les informations du défi quotidien actuel."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        today = datetime.date.today()
        # On tente de récupérer le challenge en DB ou on le crée
        challenge, created = DailyChallenge.objects.get_or_create(
            date=today,
            defaults={
                'title': f"Défi du {today}",
                'media_type': 'Anime',
                'difficulty': 'Normal',
                'description': "Le défi quotidien d'Animetix."
            }
        )
        
        return Response({
            'id': challenge.id,
            'date': challenge.date,
            'media_type': challenge.media_type,
            'difficulty': challenge.difficulty,
            'is_completed': False, # À lier aux résultats de l'utilisateur
            'reward_xp': 500
        })

class CustomConfigDataView(APIView):
    """Sert la configuration personnalisée enregistrée."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            config = getattr(request.user.profile, 'custom_config', {})
            return Response(config)
        return Response({})

class TransparencyDataView(APIView):
    """Données sur l'intégrité de l'IA et du Knowledge Graph (Public/Admin)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        container = get_container()
        # 1. Santé globale de l'inférence
        stats = container.health_dashboard_service.get_global_health()
        
        # 2. Audit du Knowledge Graph
        try:
            graph_health = container.graph_healer_service.audit_graph_quality()
            stats['knowledge_graph'] = graph_health
        except Exception as e:
            logger.warning("⚠️ Failed to audit Knowledge Graph health. Setting status as unavailable.", exc_info=True)
            stats['knowledge_graph'] = {"status": "unavailable"}

        # 3. Détection de dérive des embeddings
        try:
            drift_report = container.drift_service.get_drift_report()
            stats['embedding_drift'] = drift_report
        except Exception as e:
            logger.warning("⚠️ Failed to audit embedding drift report. Setting status as unavailable.", exc_info=True)
            stats['embedding_drift'] = {"status": "unavailable"}
            
        return Response(stats)

    def post(self, request):
        """Déclenche manuellement un cycle de nettoyage/guérison du graphe ou recalibrage drift."""
        if not request.user.is_staff:
            return Response({"error": "Admin only"}, status=403)
            
        action = request.data.get('action')
        container = get_container()
        try:
            if action == 'graph_cleanup':
                container.graph_healer_service.check_and_fix_broken_relations()
                return Response({"status": "success", "message": "Graph cleanup cycle triggered."})
            elif action == 'drift_baseline':
                coll = request.data.get('collection', 'anime')
                container.drift_service.generate_new_baseline(coll)
                return Response({"status": "success", "message": f"New baseline generated for {coll}"})
            return Response({"error": "Invalid action"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class DPOCurationView(APIView):
    """Interface de curation pour le feedback utilisateur (DPO)."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        """Liste les feedbacks négatifs nécessitant une correction humaine."""
        container = get_container()
        rejected = container.dpo_service.get_rejected_for_curation()
        return Response(rejected)

    def post(self, request):
        """Valide ou écrase une paire DPO avec une réponse 'Chosen' idéale."""
        feedback_id = request.data.get('feedback_id')
        chosen_text = request.data.get('chosen_text')
        
        from ...models import AIFeedback
        try:
            fb = AIFeedback.objects.get(id=feedback_id)
            container = get_container()
            
            # Création de la paire DPO validée
            entry = {
                'context': fb.input_context,
                'output': fb.output_text,
                'is_positive': False
            }
            dpo_pair = container.dpo_service.create_dpo_pair(entry, chosen_override=chosen_text)
            
            # Sauvegarde dans le dataset de curation validé
            project_root = settings.BASE_DIR.parent.parent
            path = project_root / "data" / "mlops" / "datasets" / "dpo_validated_curation.jsonl"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(dpo_pair, ensure_ascii=False) + '\n')
            
            # Optionnel: supprimer le feedback de la liste de curation
            fb.is_curated = True # Ajout supposé au modèle
            fb.save()
            
            return Response({"status": "success", "message": "DPO pair validated and exported."})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='dispatch')
class SpatialLabDataView(APIView):
    """Génère une carte de profondeur pour une image donnée."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import base64
        import httpx
        image_url = request.data.get('image_url')
        uploaded_file = request.FILES.get('image_file')
        
        if not image_url and not uploaded_file:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            image_data = None
            if uploaded_file:
                image_data = uploaded_file.read()
            else:
                if not is_safe_url(image_url):
                    return Response({'error': 'URL is not allowed for security reasons.'}, status=status.HTTP_403_FORBIDDEN)
                res = httpx.get(image_url, timeout=10, follow_redirects=True)
                res.raise_for_status()
                image_data = res.content
            
            depth_map_bytes = get_container().spatial_computing_service.inference_engine.estimate_depth(image_data)
            
            if not depth_map_bytes:
                return Response({'error': 'Depth estimation failed'}, status=500)
                
            depth_b64 = base64.b64encode(depth_map_bytes).decode('utf-8')
            return Response({
                'status': 'success',
                'depth_map': f"data:image/png;base64,{depth_b64}"
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='POST', block=True), name='dispatch')
class Generate3DDataView(APIView):
    """Génère un modèle 3D à partir d'une image (Gaussian Splatting/Mesh)."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import base64
        import httpx
        image_url = request.data.get('image_url')
        uploaded_file = request.FILES.get('image_file')
        mode = request.data.get('mode', 'mesh')
        
        if not image_url and not uploaded_file:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            image_data = None
            if uploaded_file:
                image_data = uploaded_file.read()
            else:
                from .utils import is_safe_url
                if not is_safe_url(image_url):
                    return Response({'error': 'URL is not allowed for security reasons.'}, status=status.HTTP_403_FORBIDDEN)
                res = httpx.get(image_url, timeout=10, follow_redirects=True)
                res.raise_for_status()
                image_data = res.content
            
            # Generate 3D model via Spatial Computing Service
            result = get_container().spatial_computing_service.generate_3d_scene(image_data, depth_map=None)
            
            return Response(result)
        except Exception as e:
            logger.error(f"Generate3D API error: {e}")
            return Response({'error': str(e)}, status=500)

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='dispatch')
class MangaLabDataView(APIView):
    """Nettoyage et traduction de bulles de manga."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import httpx
        image_url = request.data.get('image_url')
        uploaded_file = request.FILES.get('image_file')
        action = request.data.get('action', 'clean')
        
        try:
            image_data = None
            if uploaded_file:
                image_data = uploaded_file.read()
            else:
                if not is_safe_url(image_url):
                    return Response({'error': 'URL is not allowed for security reasons.'}, status=status.HTTP_403_FORBIDDEN)
                res = httpx.get(image_url, timeout=10, follow_redirects=True)
                res.raise_for_status()
                image_data = res.content
            
            if action == 'translate':
                target_lang = request.data.get('language', 'Français')
                manga_service = get_container().manga_flow_service()
                translated_img = manga_service.translate_manga_page(image_data, target_lang=target_lang)
                result = {
                    'cleaned_image': translated_img,
                    'translated_image': translated_img,
                    'bubbles': [{"box": [0, 0, 100, 100], "text": "Translated Text"}]
                }
            else:
                vision_service = get_container().vision_service()
                result = vision_service.inference_engine.process_manga_page(image_data)
            
            return Response({
                'status': 'success',
                'cleaned': result.get('cleaned_image'),
                'translated': result.get('translated_image'),
                'bubbles_found': len(result.get('bubbles', []))
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='dispatch')
class AudioLabDataView(APIView):
    """Clonage vocal XTTS."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import base64
        text = request.data.get('text', '').strip()
        voice_source = request.data.get('source_type', 'upload')
        
        if not text:
            return Response({'error': 'Texte manquant'}, status=400)
        
        try:
            ref_audio_bytes = b""
            if voice_source == 'library':
                voice_id = request.data.get('voice_id', '')
                # Sécurité : Empêcher la navigation dans les répertoires via voice_id
                safe_voice_id = os.path.basename(voice_id)
                project_root = settings.BASE_DIR.parent.parent
                path = project_root / "data" / "audio" / "library" / f"{safe_voice_id}.wav"
                if os.path.exists(path):
                    with open(path, "rb") as f: ref_audio_bytes = f.read()
            else:
                audio_file = request.FILES.get('audio_data')
                if audio_file: ref_audio_bytes = audio_file.read()

            if not ref_audio_bytes:
                return Response({'error': 'Échantillon vocal manquant'}, status=400)

            cloned_wav = get_container().voice_cloning_service.generate_character_voice(
                text=text, 
                character_audio_sample=ref_audio_bytes
            )

            if not cloned_wav:
                return Response({'error': 'Échec de la génération'}, status=500)

            from io import BytesIO
            from pydub import AudioSegment
            wav_io = BytesIO(cloned_wav)
            audio = AudioSegment.from_wav(wav_io)
            mp3_io = BytesIO()
            audio.export(mp3_io, format="mp3", bitrate="128k")
            
            res_b64 = base64.b64encode(mp3_io.getvalue()).decode('utf-8')
            return Response({
                'status': 'success',
                'audio_url': f"data:audio/mp3;base64,{res_b64}"
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class SingularityLabDataView(APIView):
    """Interact with fifth generation Evolving AI and Singularity services (SOTA 2035+)."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        action = request.data.get('action', '')
        container = get_container()

        if action == 'compile':
            function_name = request.data.get('function_name', 'cosine_similarity').strip()
            
            # Security restriction: only allow specific safe functions
            allowed_functions = ['cosine_similarity', 'euclidean_distance', 'vector_norm']
            if function_name not in allowed_functions:
                return Response({'error': f'Function "{function_name}" is not allowed for optimization.'}, status=400)
                
            try:
                optimized_fn = container.self_evolving_compiler.analyze_and_optimize(function_name)
                import numpy as np
                a = np.array([1.0, 2.0, 3.0])
                b = np.array([1.0, 2.0, 3.0])
                test_val = optimized_fn(a, b)
                
                return Response({
                    'status': 'success',
                    'message': f"Microcode pour '{function_name}' généré et compilé avec succès !",
                    'test_output': f"Calcul de {function_name} test : {test_val:.4f}",
                    'c_code_generated': f"double {function_name}_optimized(double* a, double* b, int n) {{ ... }}"
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        elif action == 'plasticity':
            activations = request.data.get('activations', [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            active_indices = request.data.get('trigger_spikes', [0, 1])
            learning_rate = float(request.data.get('learning_rate', 0.05))
            
            try:
                simulator = container.synaptic_plasticity_simulator
                
                import time
                current_time = time.time()
                simulator.trigger_spikes(active_indices, current_time)
                
                updated_W = simulator.update_hebbian(activations, learning_rate=learning_rate)
                
                stdp_log = []
                if len(active_indices) >= 2:
                    pre = active_indices[0]
                    post = active_indices[1]
                    simulator.last_spike_times[pre] = current_time - 0.05
                    simulator.last_spike_times[post] = current_time
                    dW = simulator.update_stdp(pre, post, learning_rate=learning_rate)
                    stdp_log.append(f"STDP: Connexion [{pre} -> {post}] mise à jour de {dW:+.4f}")
                
                return Response({
                    'status': 'success',
                    'message': "Plasticité synaptique neuromorphique mise à jour !",
                    'weights': updated_W.tolist(),
                    'stdp_log': stdp_log
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        elif action == 'synthesize':
            universe_name = request.data.get('universe_name', 'CyberVibe').strip()
            genre = request.data.get('genre', 'Cyberpunk').strip()
            
            try:
                synthesizer = container.autonomous_domain_synthesizer
                universe = synthesizer.synthesize_multiverse(universe_name, genre)
                
                evaluation = synthesizer.evaluate_coherence_and_interest(universe)
                persisted = synthesizer.persist_universe_to_graph(universe)
                
                return Response({
                    'status': 'success',
                    'universe': universe,
                    'evaluation': evaluation,
                    'persisted': persisted
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        else:
            return Response({'error': 'Action inconnue'}, status=400)

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='dispatch')
class VideoLabDataView(APIView):
    """Transforme une vidéo avec transfert de style SOTA (FateZero)."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        studio_style = request.data.get('studio_style', 'Ghibli')
        uploaded_file = request.FILES.get('video_file')
        if not uploaded_file:
            return Response({'error': 'No video provided'}, status=400)

        try:
            video_data = uploaded_file.read()
            service = get_container().studio_transform_service()
            # the service delegates to inference_engine
            res = service.transform_video_to_anime_sota(video_data, studio_style)
            return Response({'status': 'success', 'video_url': res})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='POST', block=True), name='dispatch')
class VideoRAGIndexView(APIView):
    """Analyse et indexe une vidéo pour la recherche sémantique temporelle."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        video_id = request.data.get('video_id')
        uploaded_file = request.FILES.get('video_file')
        
        if not video_id or not uploaded_file:
            return Response({'error': 'Missing video_id or video_file'}, status=400)
            
        try:
            video_data = uploaded_file.read()
            service = get_container().video_rag_service()
            count = service.index_video(video_id, video_data)
            return Response({
                'status': 'success', 
                'message': f'Indexed {count} temporal segments for video {video_id}.'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

@method_decorator(ratelimit(key='user_or_ip', rate='20/m', method='GET', block=True), name='dispatch')
class VideoRAGSearchView(APIView):
    """Recherche un segment précis dans la base de vidéos indexées."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')
        limit = min(int(request.query_params.get('limit', 5)), 20)
        
        if not query:
            return Response({'error': 'Missing query'}, status=400)
            
        try:
            service = get_container().video_rag_service()
            results = service.search_video_segment(query, limit=limit)
            return Response({'status': 'success', 'results': results})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='dispatch')
class SoundscapeLabDataView(APIView):
    """Génère une ambiance sonore via AudioLDM."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uploaded_file = request.FILES.get('video_file')
        if not uploaded_file:
            return Response({'error': 'No video provided'}, status=400)

        try:
            video_data = uploaded_file.read()
            service = get_container().soundscape_service()
            res = service.generate_soundscape_for_video(video_data)
            return Response({'status': 'success', 'audio_url': res})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='dispatch')
class SpeechToSpeechLabDataView(APIView):
    """Native Speech-to-Speech interaction."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import base64
        uploaded_file = request.FILES.get('audio_file')
        if not uploaded_file:
            return Response({'error': 'No audio provided'}, status=400)

        try:
            audio_data = uploaded_file.read()
            # Direct adapter call for S2S
            res_bytes = get_container().inference.audio_transformers_adapter().speech_to_speech(audio_data)
            res_b64 = base64.b64encode(res_bytes).decode('utf-8')
            return Response({'status': 'success', 'audio_url': f"data:audio/wav;base64,{res_b64}"})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


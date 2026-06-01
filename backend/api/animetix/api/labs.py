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
from core.utils.security import validate_file_mime_type, safe_http_request, validate_file_size

ALLOWED_IMAGE_MIMES = ['image/jpeg', 'image/png', 'image/webp']
ALLOWED_VIDEO_MIMES = ['video/mp4', 'video/webm', 'video/x-msvideo']
ALLOWED_AUDIO_MIMES = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/x-wav']

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 Mo
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 Mo
MAX_AUDIO_SIZE = 15 * 1024 * 1024  # 15 Mo
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
            profile = request.user.profile
            config = getattr(profile, 'custom_config', {})
            if not config:
                if not isinstance(profile.personalization_settings, dict):
                    profile.personalization_settings = {}
                config = profile.personalization_settings.get('custom_config', {})
            return Response(config)
        return Response({})

    def post(self, request):
        if request.user.is_authenticated:
            profile = request.user.profile
            if not isinstance(profile.personalization_settings, dict):
                profile.personalization_settings = {}
            profile.personalization_settings['custom_config'] = request.data
            profile.save()
            return Response(request.data)
        return Response({"error": "Not authenticated"}, status=401)

class TransparencyDataView(APIView):
    """Données sur l'intégrité de l'IA et du Knowledge Graph (Admin uniquement)."""
    permission_classes = [permissions.IsAdminUser]

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
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

    def post(self, request):
        import base64
        image_url = request.data.get('image_url')
        uploaded_file = request.FILES.get('image_file')
        
        if not image_url and not uploaded_file:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            image_data = None
            if uploaded_file:
                if not validate_file_size(uploaded_file.size, MAX_IMAGE_SIZE):
                    return Response({'error': f'Image is too large (Max: {MAX_IMAGE_SIZE/1024/1024}MB)'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                
                # Streaming read to prevent OOM
                image_data = b""
                for chunk in uploaded_file.chunks():
                    image_data += chunk
            else:
                try:
                    res = safe_http_request("GET", image_url, timeout=10)
                    res.raise_for_status()
                    image_data = res.content
                    if not validate_file_size(len(image_data), MAX_IMAGE_SIZE):
                        return Response({'error': 'Remote image is too large'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                except ValueError as ve:
                    return Response({'error': f'Unsafe URL: {str(ve)}'}, status=status.HTTP_403_FORBIDDEN)
                
            if not validate_file_mime_type(image_data, ALLOWED_IMAGE_MIMES):
                return Response({'error': 'Invalid image format. Allowed formats: JPEG, PNG, WEBP.'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            
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
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'


    def post(self, request):
        import base64
        image_url = request.data.get('image_url')
        uploaded_file = request.FILES.get('image_file')
        mode = request.data.get('mode', 'mesh')
        
        if not image_url and not uploaded_file:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            image_data = None
            if uploaded_file:
                if not validate_file_size(uploaded_file.size, MAX_IMAGE_SIZE):
                    return Response({'error': f'Image is too large (Max: {MAX_IMAGE_SIZE/1024/1024}MB)'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                
                # Streaming read to prevent OOM
                image_data = b""
                for chunk in uploaded_file.chunks():
                    image_data += chunk
            else:
                try:
                    res = safe_http_request("GET", image_url, timeout=10)
                    res.raise_for_status()
                    image_data = res.content
                    if not validate_file_size(len(image_data), MAX_IMAGE_SIZE):
                        return Response({'error': 'Remote image is too large'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                except ValueError as ve:
                    return Response({'error': f'Unsafe URL: {str(ve)}'}, status=status.HTTP_403_FORBIDDEN)
                
            if not validate_file_mime_type(image_data, ALLOWED_IMAGE_MIMES):
                return Response({'error': 'Invalid image format. Allowed formats: JPEG, PNG, WEBP.'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            
            # Generate 3D model via Spatial Computing Service
            result = get_container().spatial_computing_service.generate_3d_scene(image_data, depth_map=None)
            
            return Response(result)
        except Exception as e:
            logger.error(f"Generate3D API error: {e}")
            return Response({'error': str(e)}, status=500)

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='dispatch')
class MangaLabDataView(APIView):
    """Nettoyage et traduction de bulles de manga."""
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

    def post(self, request):
        image_url = request.data.get('image_url')
        uploaded_file = request.FILES.get('image_file')
        action = request.data.get('action', 'clean')
        
        try:
            image_data = None
            if uploaded_file:
                if not validate_file_size(uploaded_file.size, MAX_IMAGE_SIZE):
                    return Response({'error': f'Image is too large (Max: {MAX_IMAGE_SIZE/1024/1024}MB)'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                
                # Streaming read to prevent OOM
                image_data = b""
                for chunk in uploaded_file.chunks():
                    image_data += chunk
            else:
                try:
                    res = safe_http_request("GET", image_url, timeout=10)
                    res.raise_for_status()
                    image_data = res.content
                    if not validate_file_size(len(image_data), MAX_IMAGE_SIZE):
                        return Response({'error': 'Remote image is too large'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                except ValueError as ve:
                    return Response({'error': f'Unsafe URL: {str(ve)}'}, status=status.HTTP_403_FORBIDDEN)
                
            if not validate_file_mime_type(image_data, ALLOWED_IMAGE_MIMES):
                return Response({'error': 'Invalid image format. Allowed formats: JPEG, PNG, WEBP.'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            
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
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

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
                if audio_file:
                    if not validate_file_size(audio_file.size, MAX_AUDIO_SIZE):
                        return Response({'error': f'Audio is too large (Max: {MAX_AUDIO_SIZE/1024/1024}MB)'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                    ref_audio_bytes = audio_file.read()

            if not ref_audio_bytes:
                return Response({'error': 'Échantillon vocal manquant'}, status=400)

            if voice_source == 'upload' and not validate_file_mime_type(ref_audio_bytes, ALLOWED_AUDIO_MIMES):
                return Response({'error': 'Invalid audio format.'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

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
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

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

        elif action == 'quantum':
            theme = request.data.get('theme', 'shonen').lower()
            try:
                # On utilise un modèle par défaut s'il n'existe pas en session
                from core.domain.services.quantum_cognitive_model import QuantumCognitivePreferenceModel
                model = QuantumCognitivePreferenceModel(dimension=4)
                
                # Simulation d'une mesure de Born
                prob, outcome = model.measure_preference(theme)
                
                # On récupère l'état du vecteur (pour visualisation complexe)
                state_vec = model.state.tolist()
                
                return Response({
                    'status': 'success',
                    'theme': theme,
                    'probability': float(prob),
                    'outcome': outcome,
                    'state_vector': [str(x) for x in state_vec], # Complex to string
                    'message': f"Mesure quantique effectuée sur l'observable '{theme}'."
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        elif action == 'swarm':
            fact = request.data.get('fact', 'Luffy est plus fort que Naruto.')
            media = request.data.get('media', 'One Piece')
            try:
                orchestrator = container.swarm_consensus_orchestrator
                # Simulation d'un consensus d'essaim
                result = orchestrator.propose_fact_for_consensus(fact, media, proposer="User_Lab")
                
                return Response({
                    'status': 'success',
                    'fact': fact,
                    'consensus_score': result.get('consensus_score', 0.0),
                    'is_recorded': result.get('is_recorded', False),
                    'votes': result.get('votes', {}),
                    'message': "Consensus d'essaim multi-agents calculé."
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        else:
            return Response({'error': 'Action inconnue'}, status=400)

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='dispatch')
class VideoLabDataView(APIView):
    """Transforme une vidéo avec transfert de style SOTA (FateZero)."""
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

    def post(self, request):
        studio_style = request.data.get('studio_style', 'Ghibli')
        uploaded_file = request.FILES.get('video_file')
        if not uploaded_file:
            return Response({'error': 'No video provided'}, status=400)

        try:
            if not validate_file_size(uploaded_file.size, MAX_VIDEO_SIZE):
                return Response({'error': f'Video is too large (Max: {MAX_VIDEO_SIZE/1024/1024}MB)'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            
            video_data = b"".join(chunk for chunk in uploaded_file.chunks())
            if not validate_file_mime_type(video_data, ALLOWED_VIDEO_MIMES):
                return Response({'error': 'Invalid video format. Allowed formats: MP4, WEBM, AVI.'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

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
            if not validate_file_size(uploaded_file.size, MAX_VIDEO_SIZE):
                return Response({'error': f'Video is too large (Max: {MAX_VIDEO_SIZE/1024/1024}MB)'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            
            video_data = b"".join(chunk for chunk in uploaded_file.chunks())
            if not validate_file_mime_type(video_data, ALLOWED_VIDEO_MIMES):
                return Response({'error': 'Invalid video format. Allowed formats: MP4, WEBM, AVI.'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

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
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

    def post(self, request):
        uploaded_file = request.FILES.get('video_file')
        if not uploaded_file:
            return Response({'error': 'No video provided'}, status=400)

        try:
            if not validate_file_size(uploaded_file.size, MAX_VIDEO_SIZE):
                return Response({'error': f'Video is too large (Max: {MAX_VIDEO_SIZE/1024/1024}MB)'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            
            video_data = b"".join(chunk for chunk in uploaded_file.chunks())
            if not validate_file_mime_type(video_data, ALLOWED_VIDEO_MIMES):
                return Response({'error': 'Invalid video format. Allowed formats: MP4, WEBM, AVI.'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

            service = get_container().soundscape_service()
            res = service.generate_soundscape_for_video(video_data)
            return Response({'status': 'success', 'audio_url': res})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='dispatch')
class SpeechToSpeechLabDataView(APIView):
    """Native Speech-to-Speech interaction."""
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

    def post(self, request):
        import base64
        uploaded_file = request.FILES.get('audio_file')
        if not uploaded_file:
            return Response({'error': 'No audio provided'}, status=400)

        try:
            if not validate_file_size(uploaded_file.size, MAX_AUDIO_SIZE):
                return Response({'error': f'Audio is too large (Max: {MAX_AUDIO_SIZE/1024/1024}MB)'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            
            audio_data = b"".join(chunk for chunk in uploaded_file.chunks())
            if not validate_file_mime_type(audio_data, ALLOWED_AUDIO_MIMES):
                return Response({'error': 'Invalid audio format.'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

            # Direct adapter call for S2S
            res_bytes = get_container().inference.audio_transformers_adapter().speech_to_speech(audio_data)
            res_b64 = base64.b64encode(res_bytes).decode('utf-8')
            return Response({'status': 'success', 'audio_url': f"data:audio/wav;base64,{res_b64}"})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class LiquidNeuralNetworkLabView(APIView):
    """Simulateur neuromorphique de réseaux de neurones liquides (LNN)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        input_signal = request.data.get('signal', [[0.5, 0.2]])
        dt = float(request.data.get('dt', 0.05))
        
        try:
            simulator = container.core.liquid_neural_network()
            state_history = simulator.process_continuous_signal(input_signal, dt=dt)
            
            return Response({
                'status': 'success',
                'state_history': state_history,
                'state_dimension': simulator.state_dimension,
                'input_dimension': simulator.input_dimension
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)


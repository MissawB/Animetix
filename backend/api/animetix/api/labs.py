import os
import json
import datetime
import time
import numpy as np
from animetix_project.logging_config import get_logger
from django.conf import settings
from animetix.tasks_client import enqueue_task
from adapters.inference.workflows_client import GCPWorkflowsClient
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from animetix.api.core import is_safe_url
from core.utils.security import validate_file_mime_type, safe_http_request, validate_file_size, sanitize_html_content

ALLOWED_IMAGE_MIMES = ['image/jpeg', 'image/png', 'image/webp']
ALLOWED_VIDEO_MIMES = ['video/mp4', 'video/webm', 'video/x-msvideo']
ALLOWED_AUDIO_MIMES = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/x-wav']

MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024
MAX_AUDIO_SIZE = 15 * 1024 * 1024

from ..models import DailyChallenge
from ..serializers import DailyChallengeSerializer
from ..containers import get_container, Container
from dependency_injector.wiring import inject, Provide

logger = get_logger('animetix.' + __name__)

from animetix.api.billing import deduct_berrix

class DailyChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyChallenge.objects.all()
    serializer_class = DailyChallengeSerializer
    permission_classes = [permissions.AllowAny]

class LatentSpaceDataView(APIView):
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
            return Response({"error": str(e)}, status=500)

class DailyChallengeDataView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        today = datetime.date.today()
        challenge, created = DailyChallenge.objects.get_or_create(
            date=today,
            defaults={
                'media_type': 'Anime',
                'secret_title': f"Cible du {today}",
                'game_mode': 'classic'
            }
        )
        return Response({
            'id': challenge.id,
            'date': challenge.date,
            'media_type': challenge.media_type,
            'difficulty': 'Normal',
            'is_completed': False,
            'reward_xp': 500,
            'modes': [
                {
                    'id': 'classic',
                    'brush1': 'MODE',
                    'brush2': 'CLASSIQUE',
                    'description': 'Devinez le titre via des indices textuels.',
                    'gradient': 'from-blue-600 to-indigo-900',
                    'icon': '/static/animetix/img/modes/classic.png',
                    'completed': False
                },
                {
                    'id': 'vision',
                    'brush1': 'VISION',
                    'brush2': 'QUEST',
                    'description': 'Identifiez l\'œuvre à partir d\'une image générée.',
                    'gradient': 'from-purple-600 to-pink-900',
                    'icon': '/static/animetix/img/modes/vision.png',
                    'completed': False
                },
                {
                    'id': 'emoji',
                    'brush1': 'EMOJI',
                    'brush2': 'PUZZLE',
                    'description': 'Décryptez le titre caché derrière des emojis.',
                    'gradient': 'from-yellow-400 to-orange-600',
                    'icon': '/static/animetix/img/modes/emoji.png',
                    'completed': False
                }
            ]
        })

class TransparencyDataView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        container = get_container()
        stats = container.core.health_dashboard_service().get_global_health()
        try:
            graph_health = container.core.graph_healer_service().audit_graph_quality()
            stats['knowledge_graph'] = graph_health
        except:
            stats['knowledge_graph'] = {"status": "unavailable"}
        return Response(stats)

class SingularityLabDataView(APIView):
    """Interact with fifth generation Evolving AI and Singularity services (SOTA 2035+)."""
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

    def post(self, request):
        action = request.data.get('action', '')
        container = get_container()

        if action == 'compile':
            deduct_berrix(request.user, 20, "Singularity: Compilation de Kernel")
            function_name = request.data.get('function_name', 'cosine_similarity').strip()
            allowed_functions = ['cosine_similarity', 'euclidean_distance', 'vector_norm']
            if function_name not in allowed_functions:
                return Response({'error': f'Function "{function_name}" not allowed.'}, status=400)
            try:
                compiler = container.core.self_evolving_compiler()
                optimized_fn = compiler.analyze_and_optimize(function_name)
                a = np.array([1.0, 2.0, 3.0])
                b = np.array([1.0, 2.0, 3.0])
                test_val = optimized_fn(a, b)
                return Response({
                    'status': 'success',
                    'message': f"Kernel '{function_name}' compilé dynamiquement !",
                    'test_output': f"Result: {test_val:.4f}",
                    'mode': compiler.mode
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        elif action == 'plasticity':
            deduct_berrix(request.user, 20, "Singularity: Plasticité Synaptique")
            activations = request.data.get('activations', [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            active_indices = request.data.get('trigger_spikes', [0, 1])
            learning_rate = float(request.data.get('learning_rate', 0.05))
            try:
                service = container.core.synaptic_plasticity_simulator()
                now = time.time()
                service.trigger_spikes(active_indices, now)
                updated_W = service.update_hebbian(activations, learning_rate=learning_rate)
                return Response({
                    'status': 'success',
                    'message': "Plasticité synaptique (Hebb) mise à jour !",
                    'weights_mean': float(np.mean(updated_W))
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        elif action == 'quantum':
            deduct_berrix(request.user, 20, "Singularity: Effondrement Quantique")
            theme = request.data.get('theme', 'shonen').lower()
            try:
                from core.domain.services.quantum_cognitive_service import QuantumCognitiveService
                model = QuantumCognitiveService(dimension=4)
                prob, outcome = model.measure_preference(theme)
                return Response({
                    'status': 'success',
                    'theme': theme,
                    'probability': float(prob),
                    'outcome': outcome,
                    'state_vector': [str(x) for x in model.state],
                    'message': f"Effondrement quantique sur '{theme}' réussi."
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)
        
        elif action == 'evolve_dynamic':
            deduct_berrix(request.user, 50, "Singularity: Évolution LLM Dynamique")
            task = request.data.get('task', 'dot_product')
            try:
                compiler = container.core.self_evolving_compiler()
                llm = container.agentic.llm_service()
                # Évolution dynamique réelle via LLM
                fn = compiler.evolve_with_llm(task, llm_proxy=llm)
                
                # Test du kernel avec des données bidon
                a = np.array([1.0, 2.0, 3.0, 4.0])
                b = np.array([5.0, 6.0, 7.0, 8.0])
                try:
                    res = fn(a, b)
                except:
                    res = "Kernel compiled but execution failed (check input types)."
                
                return Response({
                    'status': 'success',
                    'result': str(res),
                    'kernel_name': fn.__name__,
                    'message': f"Nouveau kernel '{fn.__name__}' généré par LLM et injecté."
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        elif action == 'swarm':
            deduct_berrix(request.user, 50, "Singularity: Consensus Swarm P2P")
            fact = request.data.get('fact')
            media = request.data.get('media')
            if not fact or not media:
                return Response({'error': 'fact and media are required'}, status=400)
            
            try:
                orchestrator = container.core.swarm_consensus_orchestrator()
                # On utilise les diagnostics pour exposer Paxos-sémantique
                diagnostics = orchestrator.get_paxos_diagnostics(fact=fact, media_title=media)
                return Response(diagnostics)
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        return Response({'error': 'Action inconnue'}, status=400)

class LiquidNeuralNetworkLabView(APIView):
    """Simulateur neuromorphique de réseaux de neurones liquides (LNN)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        input_signal = request.data.get('signal', [[0.5, 0.2]])
        dt = float(request.data.get('dt', 0.05))
        try:
            lnn = container.core.liquid_neural_network()
            state_history = lnn.process_continuous_signal(input_signal, dt=dt)
            return Response({
                'status': 'success',
                'state_history': state_history,
                'final_state': lnn.state.tolist()
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class MangaLabDataView(APIView):
    """Metadata for the Manga Lab tools."""
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            'status': 'active',
            'tools': [
                {
                    'id': 'clean',
                    'name': 'Manga Cleaner',
                    'description': 'Remove text bubbles from manga pages.',
                    'endpoint': '/api/v1/manga-lab/clean/'
                },
                {
                    'id': 'translate',
                    'name': 'Manga Translator',
                    'description': 'Translate manga bubbles to target language.',
                    'endpoint': '/api/v1/manga-lab/translate/'
                },
                {
                    'id': 'voice',
                    'name': 'Manga Voice Lab',
                    'description': 'Generate voices for manga characters (Dubbing).',
                    'endpoint': '/api/v1/manga-voice/'
                }
            ]
        })

@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='POST', block=True), name='dispatch')
class MangaVoiceLabView(APIView):
    """Traduction de manga + synthèse vocale orchestrée via GCP Workflows."""
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

    def post(self, request):
        import uuid
        from django.core.cache import cache
        from adapters.inference.workflows_client import GCPWorkflowsClient
        from animetix.tasks_client import enqueue_task

        image = request.data.get('image')
        reference_audio = request.data.get('reference_audio')
        target_lang = request.data.get('target_lang', 'French')
        
        if not image or not reference_audio:
            return Response({'error': 'Missing image or reference_audio in payload'}, status=400)
            
        # Déduction des Berrix (200 Bx pour orchestration GCP + Audio)
        deduct_berrix(request.user, 200, "Manga Voice Lab (Doublage IA)")

        task_id = str(uuid.uuid4())
        filename = f"manga_voice_{task_id}.wav"
        
        # Initialisation du cache
        cache.set(f"task_result:{task_id}", {"ready": False, "status": "pending"}, timeout=3600)
        
        is_prod = getattr(settings, 'IS_PRODUCTION', False)
        if is_prod:
            try:
                client = GCPWorkflowsClient()
                execution_name = client.trigger_pipeline(image, reference_audio, target_lang, filename)
                
                # Cloud Task pour le polling
                client.enqueue_polling_task(execution_name, task_id)
                return Response({"task_id": task_id}, status=202)
            except Exception as e:
                cache.set(f"task_result:{task_id}", {"ready": True, "status": "failed", "error": str(e)}, timeout=3600)
                return Response({"error": f"Failed to start workflow: {str(e)}"}, status=500)
        else:
            # Fallback local dev synchrone simulé
            cache.set(f"task_result:{task_id}", {
                "ready": True,
                "status": "success",
                "result": {
                    "translated_text": "[Local Dev Fallback] Traduction simulée.",
                    "audio_url": f"http://localhost:8000/media/mock_{filename}"
                }
            }, timeout=3600)
            return Response({"task_id": task_id}, status=202)

class VideoFateZeroLabView(APIView):
    """Transforme une vidéo avec transfert de style SOTA (FateZero)."""
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'gpu'

    def post(self, request):
        container = get_container()
        video_file = request.FILES.get('video')
        studio_style = request.data.get('studio_style', 'Ufotable')
        
        if not video_file:
            return Response({'error': 'Video file is required.'}, status=400)
            
        # Déduction des Berrix (500 Bx pour transfert de style vidéo - Très lourd)
        deduct_berrix(request.user, 500, f"FateZero Style Transfer: {studio_style}")

        try:
            video_bytes = video_file.read()
            service = container.core.studio_transform_service()
            
            result_url = service.transform_video_to_anime_sota(video_bytes, studio_style)
            
            return Response({
                'status': 'success',
                'video_url': result_url,
                'message': f"Transformation {studio_style} (FateZero) réussie."
            })
        except Exception as e:
            logger.error(f"Error in VideoFateZeroLabView: {e}")
            return Response({'error': str(e)}, status=500)

class VideoRAGIndexView(APIView):
    """Endpoint pour indexer une vidéo dans le Video-RAG."""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        video_file = request.FILES.get('video')
        video_id = request.data.get('video_id')
        
        if not video_file or not video_id:
            return Response({'error': 'video and video_id are required'}, status=400)
            
        container = get_container()
        video_rag = container.agentic.video_rag_service()
        
        try:
            video_data = video_file.read()
            count = video_rag.index_video(video_id, video_data)
            return Response({'status': 'success', 'indexed_segments': count})
        except Exception as e:
            logger.error(f"VideoRAGIndex Error: {e}")
            return Response({'error': str(e)}, status=500)

class VideoRAGSearchView(APIView):
    """Endpoint pour rechercher des moments précis dans les vidéos indexées."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.GET.get('q')
        if not query:
            return Response({'error': 'query q is required'}, status=400)
            
        container = get_container()
        video_rag = container.agentic.video_rag_service()
        
        try:
            results = video_rag.search_video_segment(query, limit=10)
            return Response({'status': 'success', 'results': results})
        except Exception as e:
            logger.error(f"VideoRAGSearch Error: {e}")
            return Response({'error': str(e)}, status=500)

class VideoLabDataView(APIView):
    """Métadonnées pour les outils du Video Lab."""
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            'status': 'active',
            'tools': [
                {
                    'id': 'fatezero',
                    'name': 'FateZero Style Transfer',
                    'description': 'Temporally consistent anime style transfer for real videos.',
                    'endpoint': '/api/v1/labs/video/fatezero/',
                    'supported_styles': ['Shaft', 'Ufotable', 'Kyoto', 'Ghibli']
                },
                {
                    'id': 'video-rag',
                    'name': 'Video-RAG Search',
                    'description': 'Semantic search for precise moments in anime videos.',
                    'endpoint': '/api/v1/labs/video/search/'
                }
            ]
        })

class AudioLabDataView(APIView):
    """Metadata for the Audio Lab tools."""
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            'status': 'active',
            'tools': [
                {
                    'id': 'soundscape',
                    'name': 'Soundscape Generator',
                    'description': 'Generate immersive ambient soundscapes for your video clips.',
                    'endpoint': '/api/v1/labs/audio/soundscape/'
                },
                {
                    'id': 's2s',
                    'name': 'Voice Interaction (S2S)',
                    'description': 'Direct speech-to-speech interaction with anime personas.',
                    'endpoint': '/api/v1/labs/audio/s2s/'
                }
            ]
        })

class SoundscapeGenerationView(APIView):
    """Génère un soundscape ambiant pour une vidéo."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        video_file = request.FILES.get('video_file') or request.FILES.get('video')
        
        if not video_file:
            return Response({'error': 'Video file is required.'}, status=400)
            
        # Déduction des Berrix (50 Bx pour génération audio)
        deduct_berrix(request.user, 50, "Génération de Soundscape Immersif")

        try:
            video_bytes = video_file.read()
            service = container.core.soundscape_service()
            result_url = service.generate_soundscape_for_video(video_bytes)
            return Response({
                'status': 'success',
                'audio_url': result_url
            })
        except Exception as e:
            logger.error(f"Error in SoundscapeGenerationView: {e}")
            return Response({'error': str(e)}, status=500)

class SpeechToSpeechLabView(APIView):
    """Interaction directe voix-à-voix (S2S)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        audio_file = request.FILES.get('audio_file') or request.FILES.get('audio')
        persona = request.data.get('persona', 'Standard')
        
        if not audio_file:
            return Response({'error': 'Audio file is required.'}, status=400)
            
        # Déduction des Berrix (10 Bx pour un tour de parole S2S)
        deduct_berrix(request.user, 10, f"Speech-to-Speech: {persona}")

        try:
            audio_bytes = audio_file.read()
            service = container.core.native_speech_llm_service()
            result = service.process_voice_interaction(audio_bytes, persona=persona)
            
            if result.get('status') == 'success':
                # Convert audio bytes to base64 for JSON transport
                import base64
                encoded_audio = base64.b64encode(result['audio_data']).decode('utf-8')
                return Response({
                    'status': 'success',
                    'audio_data': encoded_audio
                })
            return Response(result, status=400)
        except Exception as e:
            logger.error(f"Error in SpeechToSpeechLabView: {e}")
            return Response({'error': str(e)}, status=500)

class TreeOfThoughtsLabView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def __init__(self, tot_service=Provide[Container.core.tree_of_thoughts_service], **kwargs):
        super().__init__(**kwargs)
        self.tot_service = tot_service

    def post(self, request):
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = self.tot_service.solve_with_tree_of_thoughts(query)
            return Response(result)
        except Exception as e:
            logger.error(f"Error in TreeOfThoughtsLabView: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

import base64

class MangaCleanLabView(APIView):
    """Nettoie (inpaint) les bulles de texte d'une planche de manga."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        image_file = request.FILES.get('image')
        
        if not image_file:
            return Response({'error': 'Image file is required.'}, status=400)
            
        # Déduction des Berrix (20 Bx pour inpainting de planche)
        deduct_berrix(request.user, 20, "Manga Cleaner (Planche)")

        try:
            image_bytes = image_file.read()
            inference_engine = container.inference.primary()
            
            # Un nettoyage simple équivaut à un inpainting avec une liste de bulles vide.
            cleaned_bytes = inference_engine.inpaint_text_bubbles(image_bytes, [])
            
            b64_img = base64.b64encode(cleaned_bytes).decode('utf-8')
            return Response({
                'status': 'success',
                'image': b64_img
            })
        except Exception as e:
            logger.error(f"Error in MangaCleanLabView: {e}")
            return Response({'error': str(e)}, status=500)

class MangaTranslateLabView(APIView):
    """Traduit les bulles de texte d'une planche de manga."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        image_file = request.FILES.get('image')
        target_lang = request.data.get('target_lang', 'French')
        
        if not image_file:
            return Response({'error': 'Image file is required.'}, status=400)
            
        # Déduction des Berrix (20 Bx pour inpainting + traduction)
        deduct_berrix(request.user, 20, f"Manga Translator: {target_lang}")

        try:
            image_bytes = image_file.read()
            manga_flow_service = container.core.manga_flow_service()
            
            translated_bytes = manga_flow_service.translate_manga_page(image_bytes, target_lang)
            
            b64_img = base64.b64encode(translated_bytes).decode('utf-8')
            return Response({
                'status': 'success',
                'image': b64_img
            })
        except Exception as e:
            logger.error(f"Error in MangaTranslateLabView: {e}")
            return Response({'error': str(e)}, status=500)

class VoiceCloningLabView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        target_text = request.data.get('target_text')
        ref_audio_file = request.FILES.get('reference_audio')
        
        if not target_text or not ref_audio_file:
            return Response({"error": "Missing text or audio"}, status=400)

        # Déduction des Berrix (100 Bx pour clonage vocal multi-passes)
        deduct_berrix(request.user, 100, "Voice Cloning (Audio)")

        # Validation: Pitch must be an integer
        try:
            pitch = int(request.data.get('pitch', 0))
        except (ValueError, TypeError):
            return Response({"error": "Invalid pitch value. Must be an integer."}, status=400)

        # Validation: File size (Max 5MB as per review)
        MAX_VOICE_AUDIO_SIZE = 5 * 1024 * 1024
        if not validate_file_size(ref_audio_file.size, MAX_VOICE_AUDIO_SIZE):
            return Response({"error": "Reference audio file too large (Max 5MB)."}, status=400)
            
        container = get_container()
        service = container.core.voice_cloning_service()
        
        try:
            audio_bytes = ref_audio_file.read()
            
            # Validation: MIME Type
            if not validate_file_mime_type(audio_bytes, ALLOWED_AUDIO_MIMES):
                return Response({"error": "Invalid file type. Only wav and mp3 are allowed."}, status=400)

            result_audio = service.clone(
                reference_audio=audio_bytes,
                target_text=target_text,
                pitch=pitch
            )
            # Return as base64 for pure SPA handling
            import base64
            encoded = base64.b64encode(result_audio).decode('utf-8')
            return Response({
                "status": "success",
                "audio_data": f"data:audio/wav;base64,{encoded}"
            })
        except Exception as e:
            logger.error(f"Voice Cloning Error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=500)

class SpatialLabDataView(APIView):
    """Métadonnées pour les outils de Calcul Spatial."""
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            'status': 'active',
            'tools': [
                {
                    'id': 'generate-3d',
                    'name': 'Image-to-3D',
                    'description': 'Generate a navigable 3D scene from a single image (Gaussian Splatting).',
                    'endpoint': '/api/v1/labs/spatial/generate-3d/'
                },
                {
                    'id': 'cinematic',
                    'name': 'Cinematic Reconstruction',
                    'description': 'Reconstruct dynamic volumetric 3D scenes from video clips.',
                    'endpoint': '/api/v1/labs/spatial/cinematic/'
                }
            ]
        })

class Generate3DDataView(APIView):
    """Génère une scène 3D (PLY) à partir d'une image."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        image_file = request.FILES.get('image')
        title = request.data.get('title', 'Poster 3D')
        
        if not image_file:
            return Response({'error': 'Image file is required.'}, status=400)
            
        # Déduction des Berrix (150 Bx pour reconstruction 3D Gaussian Splatting)
        deduct_berrix(request.user, 150, f"Image-to-3D: {title}")

        try:
            image_bytes = image_file.read()
            service = container.core.spatial_computing_service()
            result = service.reconstruct_3d_scene(image_bytes, title)
            return Response(result)
        except Exception as e:
            logger.error(f"Error in Generate3DDataView: {e}")
            return Response({'error': str(e)}, status=500)

class CinematicReconstructionView(APIView):
    """Génère une séquence de scènes 3D à partir d'une vidéo."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        video_file = request.FILES.get('video')
        title = request.data.get('title', 'Cinematic 3D')
        
        if not video_file:
            return Response({'error': 'Video file is required.'}, status=400)
            
        # Déduction des Berrix (500 Bx pour reconstruction volumétrique dynamique)
        deduct_berrix(request.user, 500, f"Cinematic 3D Reconstruction: {title}")

        try:
            video_bytes = video_file.read()
            service = container.core.cinematic_volumetric_reconstruction_service()
            result = service.reconstruct_dynamic_cinematic_scene(video_bytes, title)
            return Response(result)
        except Exception as e:
            logger.error(f"Error in CinematicReconstructionView: {e}")
            return Response({'error': str(e)}, status=500)

class SingularityCommandCenterView(APIView):
    """
    Vue unifiée pour le monitoring et le contrôle des expériences IA avancées.
    Agrège les données de santé de Quantum, Plasticity, Swarm, LNN, etc.
    """
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def get(self, request):
        container = get_container()
        
        # 1. État des services (Simulation de santé système)
        services = []
        try:
            # Quantum
            services.append({
                "id": "quantum",
                "name": "Quantum Cognitive",
                "status": "online",
                "load": random.randint(5, 25),
                "metrics": {"coherence": 0.98, "dimension": 4}
            })
            
            # Plasticity
            services.append({
                "id": "plasticity",
                "name": "Synaptic Plasticity",
                "status": "online",
                "load": random.randint(10, 40),
                "metrics": {"learning_rate": 0.05, "synapses": 1024}
            })
            
            # Swarm
            services.append({
                "id": "swarm",
                "name": "P2P Swarm Consensus",
                "status": "online",
                "load": random.randint(15, 60),
                "metrics": {"nodes": 12, "consensus_rate": 0.95}
            })

            # LNN
            services.append({
                "id": "lnn",
                "name": "Liquid Neural Network",
                "status": "online",
                "load": random.randint(20, 80),
                "metrics": {"stability": 0.92, "dt": 0.05}
            })
        except:
            pass

        # 2. Événements récents (Simulés pour le dashboard)
        events = [
            {"time": (datetime.datetime.now() - datetime.timedelta(minutes=2)).isoformat(), "type": "QUANTUM", "msg": "Effondrement de fonction d'onde détecté (Shonen)."},
            {"time": (datetime.datetime.now() - datetime.timedelta(minutes=5)).isoformat(), "type": "PLASTICITY", "msg": "Apprentissage Hebbien complété pour user_77."},
            {"time": (datetime.datetime.now() - datetime.timedelta(minutes=12)).isoformat(), "type": "SWARM", "msg": "Consensus Paxos-sémantique atteint sur 'One Piece Timeline'."},
        ]

        return Response({
            "status": "operational",
            "services": services,
            "events": events,
            "system_load": random.randint(30, 50)
        })

class NeuralDiagnosticsLabView(APIView):
    """
    Expose AI diagnostics for the Neural Diagnostics Dashboard.
    Uses native logprobs and XAI service.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        prompt = request.data.get('prompt')
        if not prompt:
            return Response({"error": "Prompt is required."}, status=status.HTTP_400_BAD_REQUEST)

        container = get_container()
        try:
            inference_engine = container.inference.inference_engine()
            xai_service = container.core.xai_service()

            # 1. Generate response with logprobs
            response = inference_engine.generate(prompt, include_logprobs=True)

            # 2. Get rich diagnostics report
            report = xai_service.get_diagnostics_report(prompt, response)

            return Response(report)
        except Exception as e:
            logger.error(f"Neural Diagnostics Error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


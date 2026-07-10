"""Singularity/Ghost labs: evolving-AI experiments, LNN, ToT and diagnostics."""

import datetime
import random
import time

import numpy as np
from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject  # noqa: E402
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ...containers import Container, get_container  # noqa: E402

logger = get_logger("animetix." + __name__)

from core.domain.services.berrix_economy import FEATURE_BX_COSTS  # noqa: E402

from animetix.api.billing import deduct_berrix  # noqa: E402


class SingularityLabDataView(APIView):
    """Interact with fifth generation Evolving AI and Singularity services (SOTA 2035+)."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "gpu"
    throttle_classes = [ScopedRateThrottle]

    def get(self, request):
        container = get_container()
        service = container.core.synaptic_plasticity_simulator()
        drift_service = container.core.archetype_drift_service()

        profile = getattr(request.user, "profile", None)
        settings = profile.personalization_settings if profile else {}
        drift_config = drift_service.calculate_drift(request.user.id, settings)

        return Response(
            {
                "status": "success",
                "weights": service.W.tolist(),
                "concepts": [
                    "Shonen",
                    "Seinen",
                    "Cyberpunk",
                    "Mecha",
                    "Fantasy",
                    "Magic",
                    "Ghibli",
                    "Romance",
                    "Comedy",
                    "Drama",
                ],
                "plasticity_config": {
                    "tau_plus": service.tau_plus,
                    "tau_minus": service.tau_minus,
                    "num_concepts": service.num_concepts,
                },
                "personalization_settings": settings,
                "current_archetype": {
                    "id": drift_config.archetype_id,
                    "accent": drift_config.primary_accent,
                    "aura_type": drift_config.aura_type,
                    "intensity": drift_config.aura_intensity,
                    "font_vibe": drift_config.font_vibe,
                },
            }
        )

    def post(self, request):
        action = request.data.get("action", "")
        container = get_container()

        if action == "update_config":
            profile = getattr(request.user, "profile", None)
            if profile:
                settings = profile.personalization_settings or {}
                mode = request.data.get("mode")
                if mode in ["auto", "manual"]:
                    settings["mode"] = mode
                manual_arch = request.data.get("manual_archetype")
                if manual_arch:
                    settings["manual_archetype"] = manual_arch
                intensity = request.data.get("intensity_multiplier")
                if intensity is not None:
                    try:
                        settings["intensity_multiplier"] = float(intensity)
                    except ValueError:
                        pass
                features = request.data.get("features")
                if isinstance(features, dict):
                    settings["features"] = {
                        "aura": bool(features.get("aura", True)),
                        "font": bool(features.get("font", True)),
                        "accent": bool(features.get("accent", True)),
                    }
                profile.personalization_settings = settings
                profile.save()

                # Clear cache for middleware
                from django.core.cache import cache

                cache.delete(f"personalization_drift_user_{request.user.id}")

            service = container.core.synaptic_plasticity_simulator()
            tau_plus = request.data.get("tau_plus")
            if tau_plus is not None:
                try:
                    service.tau_plus = float(tau_plus)
                except ValueError:
                    pass
            tau_minus = request.data.get("tau_minus")
            if tau_minus is not None:
                try:
                    service.tau_minus = float(tau_minus)
                except ValueError:
                    pass

            service.save_checkpoint()
            return self.get(request)

        if action == "compile":
            deduct_berrix(
                request.user,
                FEATURE_BX_COSTS["singularity_basic"],
                "Singularity: Compilation de Kernel",
            )
            function_name = request.data.get(
                "function_name", "cosine_similarity"
            ).strip()
            allowed_functions = [
                "cosine_similarity",
                "euclidean_distance",
                "vector_norm",
            ]
            if function_name not in allowed_functions:
                return Response(
                    {"error": f'Function "{function_name}" not allowed.'}, status=400
                )
            try:
                compiler = container.core.self_evolving_compiler()
                optimized_fn = compiler.analyze_and_optimize(function_name)
                a = np.array([1.0, 2.0, 3.0])
                b = np.array([1.0, 2.0, 3.0])
                test_val = optimized_fn(a, b)
                return Response(
                    {
                        "status": "success",
                        "message": f"Kernel '{function_name}' compilé dynamiquement !",
                        "test_output": f"Result: {test_val:.4f}",
                        "mode": compiler.mode,
                    }
                )
            except Exception:
                logger.exception("Error in singularity compile action")
                return Response({"error": "Internal server error"}, status=500)

        elif action == "plasticity":
            deduct_berrix(
                request.user,
                FEATURE_BX_COSTS["singularity_basic"],
                "Singularity: Plasticité Synaptique",
            )
            activations = request.data.get(
                "activations", [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            )
            active_indices = request.data.get("trigger_spikes", [0, 1])
            learning_rate = float(request.data.get("learning_rate", 0.05))
            try:
                service = container.core.synaptic_plasticity_simulator()
                now = time.time()
                service.trigger_spikes(active_indices, now)
                updated_W = service.update_hebbian(
                    activations, learning_rate=learning_rate
                )

                # Check for STDP if two specific indices provided
                stdp_log = []
                if len(active_indices) >= 2:
                    pre, post = active_indices[0], active_indices[1]
                    dW = service.update_stdp(pre, post, learning_rate=learning_rate)
                    stdp_log.append(f"STDP Update: {pre} -> {post} (dW: {dW:+.4f})")

                return Response(
                    {
                        "status": "success",
                        "message": "Plasticité synaptique synchronisée !",
                        "weights": updated_W.tolist(),
                        "weights_mean": float(np.mean(updated_W)),
                        "stdp_log": stdp_log,
                    }
                )
            except Exception:
                logger.exception("Error in singularity plasticity action")
                return Response({"error": "Internal server error"}, status=500)

        elif action == "quantum":
            deduct_berrix(
                request.user,
                FEATURE_BX_COSTS["singularity_basic"],
                "Singularity: Effondrement Quantique",
            )
            theme = request.data.get("theme", "shonen").lower()
            try:
                model = container.core.quantum_cognitive_model()
                prob, outcome = model.measure_preference(theme)
                return Response(
                    {
                        "status": "success",
                        "theme": theme,
                        "probability": float(prob),
                        "outcome": outcome,
                        "state_vector": [str(x) for x in model.state],
                        "message": f"Effondrement quantique sur '{theme}' réussi.",
                    }
                )
            except Exception:
                logger.exception("Error in singularity quantum action")
                return Response({"error": "Internal server error"}, status=500)

        elif action == "evolve_dynamic":
            deduct_berrix(
                request.user,
                FEATURE_BX_COSTS["singularity_mid"],
                "Singularity: Évolution LLM Dynamique",
            )
            task = request.data.get("task", "dot_product")
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
                except Exception:
                    res = "Kernel compiled but execution failed (check input types)."

                return Response(
                    {
                        "status": "success",
                        "result": str(res),
                        "kernel_name": fn.__name__,
                        "message": f"Nouveau kernel '{fn.__name__}' généré par LLM et injecté.",
                    }
                )
            except Exception:
                logger.exception("Error in singularity evolve_dynamic action")
                return Response({"error": "Internal server error"}, status=500)

        elif action == "swarm":
            deduct_berrix(
                request.user,
                FEATURE_BX_COSTS["singularity_mid"],
                "Singularity: Consensus Swarm P2P",
            )
            fact = request.data.get("fact")
            media = request.data.get("media")
            if not fact or not media:
                return Response({"error": "fact and media are required"}, status=400)

            try:
                orchestrator = container.core.swarm_consensus_orchestrator()
                # On utilise les diagnostics pour exposer Paxos-sémantique
                diagnostics = orchestrator.get_paxos_diagnostics(
                    fact=fact, media_title=media
                )
                return Response(diagnostics)
            except Exception:
                logger.exception("Error in singularity swarm action")
                return Response({"error": "Internal server error"}, status=500)

        elif action == "synthesize":
            deduct_berrix(
                request.user,
                FEATURE_BX_COSTS["multiverse_synth"],
                "Singularity: Synthèse Multivers",
            )
            universe_name = request.data.get("universe_name", "Unnamed Universe")
            genre = request.data.get("genre", "Cyberpunk")

            try:
                synthesizer = container.core.autonomous_domain_synthesizer()
                universe_data = synthesizer.synthesize_multiverse(
                    universe_name=universe_name, primary_genre=genre
                )

                # CRITICAL: Persist for HITL validation
                persisted = synthesizer.persist_universe_to_graph(universe_data)

                evaluation = synthesizer.evaluate_coherence_and_interest(universe_data)

                return Response(
                    {
                        "status": "success",
                        "universe": universe_data,
                        "evaluation": evaluation,
                        "persisted": persisted,
                        "message": (
                            f"Univers '{universe_name}' synthétisé et stagé pour validation."
                            if persisted
                            else f"Univers '{universe_name}' synthétisé mais rejeté par les filtres de cohérence."
                        ),
                    }
                )
            except Exception:
                logger.exception("Error in singularity synthesize action")
                return Response({"error": "Internal server error"}, status=500)

        return Response({"error": "Action inconnue"}, status=400)


class LiquidNeuralNetworkLabView(APIView):
    """Simulateur neuromorphique de réseaux de neurones liquides (LNN)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        input_signal = request.data.get("signal", [[0.5, 0.2]])
        dt = float(request.data.get("dt", 0.05))
        try:
            lnn = container.core.liquid_neural_network()
            state_history = lnn.process_continuous_signal(input_signal, dt=dt)
            return Response(
                {
                    "status": "success",
                    "state_history": state_history,
                    "final_state": lnn.state.tolist(),
                }
            )
        except Exception:
            logger.exception("Error in LiquidNeuralNetworkLabView")
            return Response({"error": "Internal server error"}, status=500)


class TreeOfThoughtsLabView(APIView):
    # GPU-backed reasoning (multi-node ToT) → requires login and consumes Berrix.
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self, tot_service=Provide[Container.core.tree_of_thoughts_service], **kwargs
    ):
        super().__init__(**kwargs)
        self.tot_service = tot_service

    def post(self, request):
        query = request.data.get("query")
        if not query:
            return Response(
                {"error": "Query required"}, status=status.HTTP_400_BAD_REQUEST
            )
        # GPU → consume Berrix (before the try so a 402 isn't swallowed into a 500).
        deduct_berrix(
            request.user, FEATURE_BX_COSTS["tree_of_thoughts"], "Tree-of-Thoughts (IA)"
        )
        try:
            result = self.tot_service.solve_with_tree_of_thoughts(query)
            return Response(result)
        except Exception:
            logger.exception("Error in TreeOfThoughtsLabView")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SingularityCommandCenterView(APIView):
    """
    Vue unifiée pour le monitoring et le contrôle des expériences IA avancées.
    Agrège les données de santé de Quantum, Plasticity, Swarm, LNN, etc.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        get_container()

        # 1. État des services (Simulation de santé système)
        services = []
        try:
            # Quantum
            services.append(
                {
                    "id": "quantum",
                    "name": "Quantum Cognitive",
                    "status": "online",
                    "load": random.randint(5, 25),  # nosec B311
                    "metrics": {"coherence": 0.98, "dimension": 4},
                }
            )

            # Plasticity
            services.append(
                {
                    "id": "plasticity",
                    "name": "Synaptic Plasticity",
                    "status": "online",
                    "load": random.randint(10, 40),
                    "metrics": {"learning_rate": 0.05, "synapses": 1024},
                }
            )

            # Swarm
            services.append(
                {
                    "id": "swarm",
                    "name": "P2P Swarm Consensus",
                    "status": "online",
                    "load": random.randint(15, 60),
                    "metrics": {"nodes": 12, "consensus_rate": 0.95},
                }
            )

            # LNN
            services.append(
                {
                    "id": "lnn",
                    "name": "Liquid Neural Network",
                    "status": "online",
                    "load": random.randint(20, 80),
                    "metrics": {"stability": 0.92, "dt": 0.05},
                }
            )
        except Exception as e:
            logger.error(f"Failed to aggregate health metrics for Ghost Labs: {e}")

        # 2. Événements récents (Simulés pour le dashboard)
        events = [
            {
                "time": (
                    datetime.datetime.now() - datetime.timedelta(minutes=2)
                ).isoformat(),
                "type": "QUANTUM",
                "msg": "Effondrement de fonction d'onde détecté (Shonen).",
            },
            {
                "time": (
                    datetime.datetime.now() - datetime.timedelta(minutes=5)
                ).isoformat(),
                "type": "PLASTICITY",
                "msg": "Apprentissage Hebbien complété pour user_77.",
            },
            {
                "time": (
                    datetime.datetime.now() - datetime.timedelta(minutes=12)
                ).isoformat(),
                "type": "SWARM",
                "msg": "Consensus Paxos-sémantique atteint sur 'One Piece Timeline'.",
            },
        ]

        return Response(
            {
                "status": "operational",
                "services": services,
                "events": events,
                "system_load": random.randint(30, 50),  # nosec B311
            }
        )


class NeuralDiagnosticsLabView(APIView):
    """
    Expose AI diagnostics for the Neural Diagnostics Dashboard.
    Uses native logprobs and XAI service.
    """

    # GPU-backed (LLM generate + logprobs) → requires login and consumes Berrix.
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        prompt = request.data.get("prompt")
        if not prompt:
            return Response(
                {"error": "Prompt is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        # GPU → consume Berrix (before the try so a 402 isn't swallowed into a 500).
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["neural_diagnostics"],
            "Neural Diagnostics (IA)",
        )

        container = get_container()
        try:
            inference_engine = container.inference.inference_engine()
            xai_service = container.core.xai_service()

            # 1. Generate response with logprobs
            response = inference_engine.generate(prompt, include_logprobs=True)

            # 2. Get rich diagnostics report
            report = xai_service.get_diagnostics_report(prompt, response)

            return Response(report)
        except Exception:
            logger.exception("Neural Diagnostics Error")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

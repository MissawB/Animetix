# -*- coding: utf-8 -*-
"""
Analyseur de dérive sémantique des datasets d'entraînement (SFT & DPO).
Compare un snapshot baseline à l'état courant du dataset pour détecter :
  - dérive de distribution thématique (topic drift)
  - changement de répartition linguistique
  - dérive de longueur des réponses
  - déséquilibre des stratégies de corruption (DPO)
  - régression de qualité (ratio de samples filtrés)
"""

import os  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import logging  # noqa: E402
from datetime import datetime  # noqa: E402
from typing import Dict, Any, Optional, List  # noqa: E402
from collections import Counter  # noqa: E402
from pydantic import BaseModel  # noqa: E402

logger = logging.getLogger("animetix.pipeline.mlops.semantic_drift_analyzer")

# --- Topic keywords for lightweight thematic fingerprinting ---
TOPIC_KEYWORDS = {
    "shonen": [
        "combat",
        "bataille",
        "tournoi",
        "puissance",
        "pouvoir",
        "entraînement",
        "fight",
        "battle",
        "power",
        "training",
        "rival",
    ],
    "seinen": [
        "mature",
        "psychologique",
        "politique",
        "survie",
        "violence",
        "adulte",
        "complex",
        "survival",
        "political",
    ],
    "shojo": [
        "romance",
        "amour",
        "sentiments",
        "relation",
        "cœur",
        "love",
        "romantic",
        "feelings",
        "heart",
    ],
    "isekai": [
        "isekai",
        "autre monde",
        "réincarné",
        "invoqué",
        "transported",
        "reincarnated",
        "another world",
    ],
    "mecha": [
        "robot",
        "mecha",
        "pilote",
        "cockpit",
        "eva",
        "gundam",
        "armure",
        "armor",
    ],
    "slice_of_life": [
        "quotidien",
        "école",
        "amitié",
        "slice of life",
        "daily",
        "school",
        "friendship",
        "lycée",
    ],
    "horror": [
        "horreur",
        "sang",
        "mort",
        "terreur",
        "horror",
        "blood",
        "death",
        "gore",
        "dark",
    ],
    "sports": [
        "sport",
        "match",
        "équipe",
        "compétition",
        "team",
        "competition",
        "basketball",
        "football",
        "volleyball",
    ],
    "fantasy": [
        "magie",
        "dragon",
        "sort",
        "sorcier",
        "elfe",
        "magic",
        "spell",
        "wizard",
        "fantasy",
    ],
    "sci_fi": [
        "espace",
        "futur",
        "technologie",
        "cyborg",
        "space",
        "future",
        "technology",
        "cyber",
        "galactique",
    ],
    "culture_otaku": [
        "otaku",
        "cosplay",
        "convention",
        "manga",
        "anime",
        "japon",
        "japan",
        "doublage",
        "seiyuu",
        "studio",
    ],
    "french_market": [
        "france",
        "français",
        "éditeur",
        "doubleur",
        "crunchyroll",
        "kana",
        "glénat",
        "adn",
        "wakanim",
    ],
}


class DatasetFingerprint(BaseModel):
    """Empreinte statistique d'un dataset d'entraînement."""

    total_samples: int
    avg_output_length: float
    median_output_length: float
    std_output_length: float
    min_output_length: int
    max_output_length: int
    language_distribution: Dict[str, float]  # {"Français": 0.7, "English": 0.3}
    topic_distribution: Dict[str, float]  # normalized topic vector
    corruption_strategy_distribution: Optional[Dict[str, float]] = None  # DPO only
    filtered_ratio: float = 0.0  # ratio of samples that failed validation
    snapshot_timestamp: str = ""


class DriftReport(BaseModel):
    """Rapport de dérive entre deux snapshots."""

    status: str  # "pass", "warning", "fail"
    overall_drift_score: float  # 0.0 = identical, 1.0 = completely different
    go_for_training: bool
    timestamp: str
    baseline_timestamp: str
    current_timestamp: str
    metrics: Dict[str, Any]
    warnings: List[str]
    blockers: List[str]


# --- Thresholds ---
DRIFT_THRESHOLDS = {
    "topic_cosine_distance": {"warning": 0.15, "block": 0.35},
    "length_shift_ratio": {"warning": 0.25, "block": 0.50},
    "language_kl_divergence": {"warning": 0.10, "block": 0.30},
    "sample_count_drop_ratio": {"warning": 0.10, "block": 0.30},
    "filtered_ratio_increase": {"warning": 0.05, "block": 0.15},
}


def _compute_topic_vector(texts: List[str]) -> Dict[str, float]:
    """Compute a normalized topic frequency vector from text samples."""
    counts = Counter()
    for text in texts:
        text_lower = text.lower()
        for topic, keywords in TOPIC_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    counts[topic] += 1
                    break  # count each topic at most once per sample

    total = sum(counts.values()) or 1
    return {topic: counts.get(topic, 0) / total for topic in TOPIC_KEYWORDS}


def _cosine_distance(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Cosine distance between two topic vectors (0 = identical, 1 = orthogonal)."""
    keys = set(list(a.keys()) + list(b.keys()))
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    norm_a = math.sqrt(sum(v**2 for v in a.values())) or 1e-9
    norm_b = math.sqrt(sum(v**2 for v in b.values())) or 1e-9
    similarity = dot / (norm_a * norm_b)
    return max(0.0, 1.0 - similarity)


def _kl_divergence(p: Dict[str, float], q: Dict[str, float]) -> float:
    """Symmetric KL divergence (Jensen-Shannon) between two distributions."""
    keys = set(list(p.keys()) + list(q.keys()))
    eps = 1e-10
    m = {k: (p.get(k, 0) + q.get(k, 0)) / 2 + eps for k in keys}
    kl_pm = sum(p.get(k, eps) * math.log((p.get(k, eps) + eps) / m[k]) for k in keys)
    kl_qm = sum(q.get(k, eps) * math.log((q.get(k, eps) + eps) / m[k]) for k in keys)
    return (kl_pm + kl_qm) / 2


def compute_fingerprint(
    dataset_path: str, dataset_type: str = "sft", filtered_count: int = 0
) -> DatasetFingerprint:
    """
    Compute a statistical fingerprint from a JSONL dataset.

    Args:
        dataset_path: Path to the JSONL file
        dataset_type: "sft" or "dpo"
        filtered_count: Number of samples that were filtered out during compilation
    """
    samples = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not samples:
        return DatasetFingerprint(
            total_samples=0,
            avg_output_length=0,
            median_output_length=0,
            std_output_length=0,
            min_output_length=0,
            max_output_length=0,
            language_distribution={},
            topic_distribution={},
            filtered_ratio=1.0,
            snapshot_timestamp=datetime.now().isoformat(),
        )

    # Extract output texts
    if dataset_type == "dpo":
        output_texts = [s.get("chosen", "") for s in samples]
        prompt_texts = [s.get("prompt", "") for s in samples]
        all_texts = output_texts + prompt_texts
    else:
        output_texts = [s.get("output", "") for s in samples]
        prompt_texts = [s.get("instruction", "") for s in samples]
        all_texts = output_texts + prompt_texts

    # Length statistics
    lengths = [len(t) for t in output_texts]
    sorted_lengths = sorted(lengths)
    n = len(sorted_lengths)

    avg_len = sum(lengths) / n
    median_len = (
        sorted_lengths[n // 2]
        if n % 2 == 1
        else (sorted_lengths[n // 2 - 1] + sorted_lengths[n // 2]) / 2
    )
    variance = sum((length - avg_len) ** 2 for length in lengths) / n
    std_len = math.sqrt(variance)

    # Language distribution
    lang_counts = Counter()
    for s in samples:
        lang = s.get("language", "unknown")
        lang_counts[lang] += 1
    total = sum(lang_counts.values()) or 1
    lang_dist = {lang: count / total for lang, count in lang_counts.items()}

    # Topic distribution
    topic_dist = _compute_topic_vector(all_texts)

    # Corruption strategy distribution (DPO only)
    corruption_dist = None
    if dataset_type == "dpo":
        # Infer strategy from rejected text patterns
        strategy_counts = Counter()
        for s in samples:
            rejected = s.get("rejected", "")
            chosen = s.get("chosen", "")
            if any(
                kw in rejected.lower()
                for kw in [
                    "désolé",
                    "aucune idée",
                    "sorry",
                    "don't know",
                    "cherche sur google",
                ]
            ):
                strategy_counts["refusal"] += 1
            elif any(
                kw in rejected.lower()
                for kw in [
                    "basically",
                    "literally",
                    "fr fr",
                    "actually",
                    "évident",
                    "triviale",
                    "répète",
                    "honestly",
                    "condescend",
                ]
            ):
                strategy_counts["tone"] += 1
            elif len(rejected) < len(chosen) * 0.75:
                strategy_counts["truncation"] += 1
            else:
                strategy_counts["fact_or_llm"] += 1

        strat_total = sum(strategy_counts.values()) or 1
        corruption_dist = {k: v / strat_total for k, v in strategy_counts.items()}

    # Filtered ratio
    total_attempted = len(samples) + filtered_count
    filtered_ratio = filtered_count / total_attempted if total_attempted > 0 else 0.0

    return DatasetFingerprint(
        total_samples=len(samples),
        avg_output_length=round(avg_len, 2),
        median_output_length=round(median_len, 2),
        std_output_length=round(std_len, 2),
        min_output_length=min(lengths),
        max_output_length=max(lengths),
        language_distribution=lang_dist,
        topic_distribution=topic_dist,
        corruption_strategy_distribution=corruption_dist,
        filtered_ratio=round(filtered_ratio, 4),
        snapshot_timestamp=datetime.now().isoformat(),
    )


def save_baseline(fingerprint: DatasetFingerprint, output_path: str):
    """Save a fingerprint as the baseline snapshot."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fingerprint.model_dump(), f, ensure_ascii=False, indent=2)
    logger.info(f"Baseline fingerprint saved to {output_path}")


def load_baseline(baseline_path: str) -> Optional[DatasetFingerprint]:
    """Load a previously saved baseline fingerprint."""
    if not os.path.exists(baseline_path):
        return None
    try:
        with open(baseline_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return DatasetFingerprint.model_validate(data)
    except Exception as e:
        logger.warning(f"Failed to load baseline: {e}")
        return None


def analyze_drift(
    current: DatasetFingerprint, baseline: DatasetFingerprint
) -> DriftReport:
    """
    Compare current fingerprint against baseline and produce a drift report.
    Returns a go/no-go verdict for launching training.
    """
    warnings = []
    blockers = []
    metrics = {}

    # 1. Topic drift (cosine distance)
    topic_distance = _cosine_distance(
        current.topic_distribution, baseline.topic_distribution
    )
    metrics["topic_cosine_distance"] = round(topic_distance, 4)
    t = DRIFT_THRESHOLDS["topic_cosine_distance"]
    if topic_distance >= t["block"]:
        blockers.append(
            f"Dérive thématique critique : cosine distance = {topic_distance:.3f} (seuil bloquant = {t['block']})"
        )
    elif topic_distance >= t["warning"]:
        warnings.append(
            f"Dérive thématique détectée : cosine distance = {topic_distance:.3f} (seuil d'alerte = {t['warning']})"
        )

    # 2. Length shift
    if baseline.avg_output_length > 0:
        length_shift = (
            abs(current.avg_output_length - baseline.avg_output_length)
            / baseline.avg_output_length
        )
    else:
        length_shift = 0.0
    metrics["length_shift_ratio"] = round(length_shift, 4)
    t = DRIFT_THRESHOLDS["length_shift_ratio"]
    if length_shift >= t["block"]:
        blockers.append(
            f"Dérive de longueur critique : shift = {length_shift:.1%} (seuil bloquant = {t['block']:.0%})"
        )
    elif length_shift >= t["warning"]:
        warnings.append(
            f"Dérive de longueur détectée : shift = {length_shift:.1%} (seuil d'alerte = {t['warning']:.0%})"
        )

    # 3. Language distribution drift (Jensen-Shannon divergence)
    lang_div = _kl_divergence(
        current.language_distribution, baseline.language_distribution
    )
    metrics["language_js_divergence"] = round(lang_div, 4)
    t = DRIFT_THRESHOLDS["language_kl_divergence"]
    if lang_div >= t["block"]:
        blockers.append(
            f"Dérive linguistique critique : JS divergence = {lang_div:.3f} (seuil bloquant = {t['block']})"
        )
    elif lang_div >= t["warning"]:
        warnings.append(
            f"Dérive linguistique détectée : JS divergence = {lang_div:.3f} (seuil d'alerte = {t['warning']})"
        )

    # 4. Sample count drop
    if baseline.total_samples > 0:
        count_drop = (
            baseline.total_samples - current.total_samples
        ) / baseline.total_samples
    else:
        count_drop = 0.0
    count_drop = max(0.0, count_drop)  # only care about drops, not increases
    metrics["sample_count_drop_ratio"] = round(count_drop, 4)
    t = DRIFT_THRESHOLDS["sample_count_drop_ratio"]
    if count_drop >= t["block"]:
        blockers.append(
            f"Perte d'échantillons critique : -{count_drop:.1%} (seuil bloquant = {t['block']:.0%})"
        )
    elif count_drop >= t["warning"]:
        warnings.append(
            f"Perte d'échantillons détectée : -{count_drop:.1%} (seuil d'alerte = {t['warning']:.0%})"
        )

    # 5. Filtered ratio increase
    filtered_increase = current.filtered_ratio - baseline.filtered_ratio
    filtered_increase = max(0.0, filtered_increase)
    metrics["filtered_ratio_increase"] = round(filtered_increase, 4)
    t = DRIFT_THRESHOLDS["filtered_ratio_increase"]
    if filtered_increase >= t["block"]:
        blockers.append(
            f"Augmentation critique du taux de filtrage : +{filtered_increase:.1%} (seuil bloquant = {t['block']:.0%})"
        )
    elif filtered_increase >= t["warning"]:
        warnings.append(
            f"Augmentation du taux de filtrage : +{filtered_increase:.1%} (seuil d'alerte = {t['warning']:.0%})"
        )

    # Overall drift score (weighted average of normalized metrics)
    weights = {
        "topic": 0.35,
        "length": 0.20,
        "language": 0.20,
        "count": 0.15,
        "filtered": 0.10,
    }
    normalized = {
        "topic": min(
            1.0, topic_distance / DRIFT_THRESHOLDS["topic_cosine_distance"]["block"]
        ),
        "length": min(
            1.0, length_shift / DRIFT_THRESHOLDS["length_shift_ratio"]["block"]
        ),
        "language": min(
            1.0, lang_div / DRIFT_THRESHOLDS["language_kl_divergence"]["block"]
        ),
        "count": min(
            1.0, count_drop / DRIFT_THRESHOLDS["sample_count_drop_ratio"]["block"]
        ),
        "filtered": min(
            1.0,
            filtered_increase / DRIFT_THRESHOLDS["filtered_ratio_increase"]["block"],
        ),
    }
    overall = sum(normalized[k] * weights[k] for k in weights)

    # Verdict
    if blockers:
        status = "fail"
        go = False
    elif warnings:
        status = "warning"
        go = True  # warnings don't block, but are logged
    else:
        status = "pass"
        go = True

    now = datetime.now().isoformat()
    return DriftReport(
        status=status,
        overall_drift_score=round(overall, 4),
        go_for_training=go,
        timestamp=now,
        baseline_timestamp=baseline.snapshot_timestamp,
        current_timestamp=current.snapshot_timestamp,
        metrics=metrics,
        warnings=warnings,
        blockers=blockers,
    )


def run_pre_training_drift_check(
    dataset_path: str,
    baseline_path: str,
    report_output_dir: str,
    dataset_type: str = "sft",
    filtered_count: int = 0,
    auto_update_baseline: bool = False,
) -> DriftReport:
    """
    Entry point: runs drift analysis before a training launch.

    Args:
        dataset_path: Path to the current JSONL dataset
        baseline_path: Path to the baseline fingerprint JSON
        report_output_dir: Directory to save the drift report
        dataset_type: "sft" or "dpo"
        filtered_count: Number of samples filtered during compilation
        auto_update_baseline: If True, update baseline on pass

    Returns:
        DriftReport with go/no-go verdict
    """
    logger.info(f"Computing fingerprint for {dataset_path}...")
    current = compute_fingerprint(dataset_path, dataset_type, filtered_count)

    baseline = load_baseline(baseline_path)
    if baseline is None:
        logger.info("No baseline found — saving current as baseline.")
        save_baseline(current, baseline_path)
        report = DriftReport(
            status="pass",
            overall_drift_score=0.0,
            go_for_training=True,
            timestamp=datetime.now().isoformat(),
            baseline_timestamp=current.snapshot_timestamp,
            current_timestamp=current.snapshot_timestamp,
            metrics={"info": "First run — baseline initialized."},
            warnings=[],
            blockers=[],
        )
    else:
        report = analyze_drift(current, baseline)

    # Save report
    os.makedirs(report_output_dir, exist_ok=True)
    report_file = os.path.join(
        report_output_dir,
        f"drift_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)
    logger.info(f"Drift report saved to {report_file}")

    # Log verdict
    if report.go_for_training:
        logger.info(
            f"✅ Drift check PASSED (score={report.overall_drift_score:.3f}). Safe to proceed with training."
        )
    else:
        logger.warning(
            f"❌ Drift check FAILED (score={report.overall_drift_score:.3f}). Training should NOT proceed."
        )
        for b in report.blockers:
            logger.warning(f"  BLOCKER: {b}")

    for w in report.warnings:
        logger.warning(f"  WARNING: {w}")

    # Auto-update baseline on pass
    if auto_update_baseline and report.status == "pass":
        save_baseline(current, baseline_path)
        logger.info("Baseline auto-updated after successful drift check.")

    return report

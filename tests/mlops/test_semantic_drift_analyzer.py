# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest


class TestDatasetFingerprint(unittest.TestCase):
    """Tests for dataset fingerprint computation."""

    def _write_sft_dataset(self, tmpdir, entries):
        path = os.path.join(tmpdir, "sft.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        return path

    def _write_dpo_dataset(self, tmpdir, entries):
        path = os.path.join(tmpdir, "dpo.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        return path

    def test_sft_fingerprint_basic(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            compute_fingerprint,
        )

        entries = [
            {
                "instruction": "Parle de Naruto.",
                "output": "Naruto est un manga shonen de combat créé par Masashi Kishimoto.",
                "language": "Français",
            },
            {
                "instruction": "Tell me about One Piece.",
                "output": "One Piece is a shonen manga by Eiichiro Oda about pirates.",
                "language": "English",
            },
            {
                "instruction": "Quel studio a fait Evangelion ?",
                "output": "Le studio Gainax a produit Neon Genesis Evangelion, un anime mecha culte.",
                "language": "Français",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._write_sft_dataset(tmpdir, entries)
            fp = compute_fingerprint(path, dataset_type="sft")

            self.assertEqual(fp.total_samples, 3)
            self.assertGreater(fp.avg_output_length, 0)
            self.assertAlmostEqual(
                fp.language_distribution["Français"], 2 / 3, places=2
            )
            self.assertAlmostEqual(fp.language_distribution["English"], 1 / 3, places=2)
            # Topic distribution should detect shonen and mecha
            self.assertGreater(fp.topic_distribution.get("shonen", 0), 0)
            self.assertGreater(fp.topic_distribution.get("mecha", 0), 0)
            self.assertIsNotNone(fp.snapshot_timestamp)

    def test_dpo_fingerprint_with_corruption_detection(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            compute_fingerprint,
        )

        entries = [
            {
                "prompt": "Q1",
                "chosen": "Réponse longue et détaillée sur l'anime Dragon Ball Z avec combat et puissance.",
                "rejected": "Désolé, je ne dispose pas de ces informations.",
            },
            {
                "prompt": "Q2",
                "chosen": "Texte correct sur le studio MAPPA et la production de Jujutsu Kaisen.",
                "rejected": "Texte court",
            },
            {
                "prompt": "Q3",
                "chosen": "Réponse complète sur le manga Berserk et sa violence mature.",
                "rejected": "Basically, c'est literally un anime, fr fr.",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._write_dpo_dataset(tmpdir, entries)
            fp = compute_fingerprint(path, dataset_type="dpo")

            self.assertEqual(fp.total_samples, 3)
            self.assertIsNotNone(fp.corruption_strategy_distribution)
            # Should detect at least refusal and tone strategies
            self.assertGreater(fp.corruption_strategy_distribution.get("refusal", 0), 0)
            self.assertGreater(fp.corruption_strategy_distribution.get("tone", 0), 0)

    def test_empty_dataset_fingerprint(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            compute_fingerprint,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "empty.jsonl")
            with open(path, "w"):
                pass

            fp = compute_fingerprint(path, dataset_type="sft")
            self.assertEqual(fp.total_samples, 0)
            self.assertEqual(fp.filtered_ratio, 1.0)

    def test_filtered_ratio_computation(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            compute_fingerprint,
        )

        entries = [
            {
                "instruction": "Q",
                "output": "Réponse correcte avec assez de caractères.",
                "language": "Français",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._write_sft_dataset(tmpdir, entries)
            fp = compute_fingerprint(path, dataset_type="sft", filtered_count=4)
            # 1 kept + 4 filtered = 5 total, filtered_ratio = 4/5 = 0.8
            self.assertAlmostEqual(fp.filtered_ratio, 0.8, places=2)


class TestDriftAnalysis(unittest.TestCase):
    """Tests for drift comparison between baseline and current."""

    def _make_fingerprint(self, **kwargs):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            DatasetFingerprint,
        )

        defaults = {
            "total_samples": 1000,
            "avg_output_length": 200.0,
            "median_output_length": 180.0,
            "std_output_length": 50.0,
            "min_output_length": 40,
            "max_output_length": 500,
            "language_distribution": {"Français": 0.7, "English": 0.3},
            "topic_distribution": {
                "shonen": 0.25,
                "seinen": 0.15,
                "shojo": 0.10,
                "isekai": 0.10,
                "mecha": 0.05,
                "slice_of_life": 0.10,
                "horror": 0.05,
                "sports": 0.05,
                "fantasy": 0.05,
                "sci_fi": 0.05,
                "culture_otaku": 0.03,
                "french_market": 0.02,
            },
            "filtered_ratio": 0.02,
            "snapshot_timestamp": "2026-06-01T00:00:00",
        }
        defaults.update(kwargs)
        return DatasetFingerprint(**defaults)

    def test_identical_datasets_pass(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            analyze_drift,
        )

        baseline = self._make_fingerprint()
        current = self._make_fingerprint(snapshot_timestamp="2026-06-12T00:00:00")

        report = analyze_drift(current, baseline)
        self.assertEqual(report.status, "pass")
        self.assertTrue(report.go_for_training)
        self.assertAlmostEqual(report.overall_drift_score, 0.0, places=2)
        self.assertEqual(len(report.blockers), 0)
        self.assertEqual(len(report.warnings), 0)

    def test_topic_drift_warning(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            analyze_drift,
        )

        baseline = self._make_fingerprint()
        # Shift topic distribution toward isekai/fantasy
        shifted_topics = {
            "shonen": 0.10,
            "seinen": 0.05,
            "shojo": 0.05,
            "isekai": 0.30,
            "mecha": 0.02,
            "slice_of_life": 0.05,
            "horror": 0.03,
            "sports": 0.02,
            "fantasy": 0.25,
            "sci_fi": 0.05,
            "culture_otaku": 0.05,
            "french_market": 0.03,
        }
        current = self._make_fingerprint(
            topic_distribution=shifted_topics, snapshot_timestamp="2026-06-12"
        )

        report = analyze_drift(current, baseline)
        self.assertIn(report.status, ["warning", "fail"])
        self.assertGreater(report.metrics["topic_cosine_distance"], 0.10)

    def test_length_drift_blocker(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            analyze_drift,
        )

        baseline = self._make_fingerprint(avg_output_length=200.0)
        # Dramatically shorter outputs
        current = self._make_fingerprint(
            avg_output_length=80.0, snapshot_timestamp="2026-06-12"
        )

        report = analyze_drift(current, baseline)
        self.assertEqual(report.status, "fail")
        self.assertFalse(report.go_for_training)
        self.assertGreater(len(report.blockers), 0)

    def test_sample_count_drop_blocker(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            analyze_drift,
        )

        baseline = self._make_fingerprint(total_samples=1000)
        current = self._make_fingerprint(
            total_samples=500, snapshot_timestamp="2026-06-12"
        )

        report = analyze_drift(current, baseline)
        self.assertEqual(report.status, "fail")
        self.assertFalse(report.go_for_training)

    def test_sample_count_increase_no_alarm(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            analyze_drift,
        )

        baseline = self._make_fingerprint(total_samples=1000)
        current = self._make_fingerprint(
            total_samples=1500, snapshot_timestamp="2026-06-12"
        )

        report = analyze_drift(current, baseline)
        # Increase is fine — only drops matter
        self.assertEqual(report.metrics["sample_count_drop_ratio"], 0.0)

    def test_filtered_ratio_spike_warning(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            analyze_drift,
        )

        baseline = self._make_fingerprint(filtered_ratio=0.02)
        current = self._make_fingerprint(
            filtered_ratio=0.10, snapshot_timestamp="2026-06-12"
        )

        report = analyze_drift(current, baseline)
        self.assertIn("warning", report.status)
        self.assertGreater(len(report.warnings), 0)


class TestBaselinePersistence(unittest.TestCase):
    """Tests for saving/loading baseline fingerprints."""

    def test_save_and_load_baseline(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            DatasetFingerprint,
            load_baseline,
            save_baseline,
        )

        fp = DatasetFingerprint(
            total_samples=100,
            avg_output_length=200.0,
            median_output_length=180.0,
            std_output_length=50.0,
            min_output_length=40,
            max_output_length=500,
            language_distribution={"Français": 0.8, "English": 0.2},
            topic_distribution={"shonen": 0.5, "seinen": 0.5},
            filtered_ratio=0.01,
            snapshot_timestamp="2026-06-01T00:00:00",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "baseline.json")
            save_baseline(fp, path)

            loaded = load_baseline(path)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.total_samples, 100)
            self.assertAlmostEqual(loaded.language_distribution["Français"], 0.8)
            self.assertEqual(loaded.snapshot_timestamp, "2026-06-01T00:00:00")

    def test_load_missing_baseline_returns_none(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            load_baseline,
        )

        result = load_baseline("/nonexistent/path/baseline.json")
        self.assertIsNone(result)


class TestEndToEnd(unittest.TestCase):
    """Integration test for the full pre-training drift check."""

    def test_first_run_creates_baseline_and_passes(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            run_pre_training_drift_check,
        )

        entries = [
            {
                "instruction": "Parle de Naruto.",
                "output": "Naruto est un manga shonen de combat très populaire.",
                "language": "Français",
            },
            {
                "instruction": "What is One Piece?",
                "output": "One Piece is a shonen manga by Eiichiro Oda.",
                "language": "English",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            sft_path = os.path.join(tmpdir, "sft.jsonl")
            baseline_path = os.path.join(tmpdir, "baseline.json")

            with open(sft_path, "w", encoding="utf-8") as f:
                for e in entries:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")

            report = run_pre_training_drift_check(
                dataset_path=sft_path,
                baseline_path=baseline_path,
                report_output_dir=tmpdir,
                dataset_type="sft",
            )

            self.assertEqual(report.status, "pass")
            self.assertTrue(report.go_for_training)
            # Baseline should now exist
            self.assertTrue(os.path.exists(baseline_path))
            # Report file should exist
            report_files = [
                f for f in os.listdir(tmpdir) if f.startswith("drift_analysis_")
            ]
            self.assertEqual(len(report_files), 1)

    def test_second_run_with_stable_data_passes(self):
        from backend.pipeline.mlops.semantic_drift_analyzer import (  # noqa: E402
            run_pre_training_drift_check,
        )

        entries = [
            {
                "instruction": "Parle de Naruto.",
                "output": "Naruto est un manga shonen de combat très populaire.",
                "language": "Français",
            },
            {
                "instruction": "What is One Piece?",
                "output": "One Piece is a shonen manga by Eiichiro Oda.",
                "language": "English",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            sft_path = os.path.join(tmpdir, "sft.jsonl")
            baseline_path = os.path.join(tmpdir, "baseline.json")

            with open(sft_path, "w", encoding="utf-8") as f:
                for e in entries:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")

            # First run — creates baseline
            run_pre_training_drift_check(sft_path, baseline_path, tmpdir, "sft")

            # Second run — same data, should pass
            report = run_pre_training_drift_check(
                sft_path, baseline_path, tmpdir, "sft"
            )
            self.assertEqual(report.status, "pass")
            self.assertTrue(report.go_for_training)
            self.assertAlmostEqual(report.overall_drift_score, 0.0, places=2)


if __name__ == "__main__":
    unittest.main()

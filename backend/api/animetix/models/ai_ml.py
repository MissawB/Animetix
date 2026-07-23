import json

from django.contrib.auth.models import User
from django.db import models


class AIFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    feedback_type = models.CharField(max_length=50)
    input_context = models.TextField(default="")
    output_text = models.TextField(default="")
    is_positive = models.BooleanField()
    is_ignored = models.BooleanField(default=False)
    weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.feedback_type} ({'IGNORED' if self.is_ignored else 'ACTIVE'})"


class AIREvalResult(models.Model):
    game_mode = models.CharField(max_length=50, default="classic")
    input_context = models.TextField(default="")
    output_text = models.TextField(default="")
    faithfulness = models.FloatField(default=0.0)
    relevancy = models.FloatField(default=0.0)
    precision = models.FloatField(default=0.0)
    hallucination_detected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class GoldDatasetEntry(models.Model):
    ENTRY_TYPES = [
        ("QA", "Question-Answering"),
        ("MULTIVERSE", "Synthetic Universe"),
        ("DISTILLATION", "Model Distillation"),
        ("OTHER", "Other Synthetic Data"),
    ]

    context = models.TextField()
    instruction = models.TextField()
    response = models.TextField()

    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default="QA")
    metadata = models.JSONField(default=dict, blank=True)

    source_feedback = models.OneToOneField(
        AIFeedback, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_validated = models.BooleanField(default=False)

    ai_validation_score = models.FloatField(default=0.0)
    ai_critique = models.TextField(null=True, blank=True)
    confidence_score = models.FloatField(default=0.0)
    is_safe = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gold Entry {self.id} ({self.entry_type}) - {self.instruction[:30]}..."


class AISafetyEvent(models.Model):
    EVENT_TYPES = [
        ("input", "Entrée Utilisateur"),
        ("output", "Sortie Assistant"),
        ("system", "Système"),
    ]
    ACTIONS = [
        ("block", "Bloqué"),
        ("warn", "Avertissement"),
        ("rewrite", "Réécriture"),
        ("none", "Aucune"),
    ]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    action = models.CharField(max_length=20, choices=ACTIONS)
    detected_categories = models.JSONField(default=list)

    input_text = models.TextField(null=True, blank=True)
    output_text = models.TextField(null=True, blank=True)
    reasoning = models.TextField(null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Safety {self.event_type} - {self.action} ({self.created_at})"


class DriftBaseline(models.Model):
    collection_name = models.CharField(max_length=50, unique=True)
    norms = models.JSONField(default=list)
    sample_size = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DriftBaseline {self.collection_name} ({self.sample_size} vecteurs)"


class SemanticCache(models.Model):
    query_text = models.TextField(unique=True)
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.query_text[:50]


class DataCurationTicket(models.Model):
    item_title = models.CharField(max_length=255)
    issue_description = models.TextField()
    source_pg = models.JSONField(default=dict)
    source_neo4j = models.JSONField(default=dict)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.id}: {self.item_title}"


class AITokenUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    engine = models.CharField(max_length=50)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    allocated_budget = models.IntegerField(default=0)
    cost_estimate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.engine} usage by {self.user.username if self.user else 'Guest'}"


class LatentSpacePoint(models.Model):
    media_type = models.CharField(max_length=20)
    vibe_type = models.CharField(max_length=20)
    external_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    x = models.FloatField()
    y = models.FloatField()
    z = models.FloatField()
    cluster = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("media_type", "vibe_type", "external_id")
        indexes = [
            models.Index(fields=["media_type", "vibe_type"]),
        ]

    def __str__(self):
        return f"{self.media_type} - {self.vibe_type} - {self.title}"


class PGVectorField(models.Field):
    description = "Vector representation compatible with pgvector (PostgreSQL) and JSON strings (SQLite)"

    def db_type(self, connection):
        if connection.vendor == "postgresql":
            return "vector"
        return "text"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def to_python(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, list):
            return "[" + ",".join(map(str, value)) + "]"
        return value


class VectorRecord(models.Model):
    collection_name = models.CharField(max_length=100, db_index=True)
    item_id = models.CharField(max_length=100, db_index=True)
    embedding = PGVectorField()
    metadata = models.JSONField(default=dict, blank=True)
    document = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("collection_name", "item_id")
        indexes = [
            models.Index(fields=["collection_name", "item_id"]),
        ]

    def __str__(self):
        return f"{self.collection_name} - {self.item_id}"


class VoiceProfile(models.Model):
    ORIGIN_CHOICES = [
        ("dataset", "Dataset (Hugging Face)"),
        ("youtube", "YouTube Ingestion"),
        ("upload", "Manual Upload"),
    ]
    LANGUAGE_CHOICES = [
        ("japanese", "Japanese (Seiyuu)"),
        ("french", "French (Doubleur)"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=255, unique=True)
    language = models.CharField(
        max_length=20, choices=LANGUAGE_CHOICES, default="japanese"
    )
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES, default="dataset")
    definition = models.TextField(null=True, blank=True)
    roles = models.TextField(null=True, blank=True)
    impact = models.CharField(max_length=100, null=True, blank=True)
    origin_detail = models.CharField(max_length=500, null=True, blank=True)
    sample_file = models.FileField(upload_to="audio/samples/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_language_display()})"

    @property
    def sample_url(self) -> str:
        if self.sample_file:
            return self.sample_file.url
        if self.origin_detail and self.origin_detail.startswith("http"):
            try:
                from core.utils.security import safe_http_request
                from django.core.files.base import ContentFile
                from django.utils.text import slugify

                response = safe_http_request("GET", self.origin_detail, timeout=10)
                if response.status_code == 200:
                    file_name = f"{slugify(self.name)}_sample.wav"
                    self.sample_file.save(
                        file_name, ContentFile(response.content), save=True
                    )
                    return self.sample_file.url
            except Exception as e:
                import logging

                logging.getLogger("animetix.models").warning(
                    f"Failed to fetch/save voice sample from {self.origin_detail}: {e}"
                )
            return self.origin_detail
        return ""

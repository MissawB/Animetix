from rest_framework import serializers

from ..models import (
    AIFeedback,
    AIREvalResult,
    AISafetyEvent,
    DataCurationTicket,
    GoldDatasetEntry,
    VoiceProfile,
)


class DocumentAttributionSerializer(serializers.Serializer):
    title = serializers.CharField()
    contribution_weight = serializers.FloatField()
    relevance_score = serializers.FloatField(required=False)
    document_id = serializers.CharField(required=False)


class LogitLensTrajectorySerializer(serializers.Serializer):
    layer = serializers.IntegerField()
    top_tokens = serializers.ListField(child=serializers.CharField())
    internal_probabilities = serializers.ListField(child=serializers.FloatField())


class ModelDiagnosticsSerializer(serializers.Serializer):
    attention_heatmap = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField())
    )
    top_influential_tokens = serializers.ListField(child=serializers.CharField())
    logit_lens_trajectory = LogitLensTrajectorySerializer(many=True)


class UncertaintySerializer(serializers.Serializer):
    confidence_score = serializers.FloatField()
    is_reliable = serializers.BooleanField()
    perplexity = serializers.FloatField(allow_null=True)
    action_required = serializers.CharField()
    method = serializers.CharField()


class AgentTraceStepSerializer(serializers.Serializer):
    agent = serializers.CharField()
    thought = serializers.CharField()


class XaiReportSerializer(serializers.Serializer):
    query_intent = serializers.CharField()
    retrieval_attribution = DocumentAttributionSerializer(many=True, required=False)
    internal_diagnostics = ModelDiagnosticsSerializer(required=False)
    uncertainty = UncertaintySerializer(required=False)
    agent_trace = AgentTraceStepSerializer(many=True, required=False)
    final_confidence = serializers.FloatField()


class AISafetyEventSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = AISafetyEvent
        fields = [
            "id",
            "event_type",
            "action",
            "detected_categories",
            "input_text",
            "output_text",
            "reasoning",
            "user",
            "username",
            "created_at",
        ]


class AIREvalResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIREvalResult
        fields = "__all__"


class GoldDatasetEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldDatasetEntry
        fields = "__all__"


class AIFeedbackSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = AIFeedback
        fields = "__all__"


class DataCurationTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCurationTicket
        fields = "__all__"


class AIFeedbackInputSerializer(serializers.Serializer):
    is_positive = serializers.BooleanField()
    type = serializers.CharField(required=False, default="general")
    input_context = serializers.CharField(required=False, allow_blank=True)
    context = serializers.CharField(required=False, allow_blank=True)
    query = serializers.CharField(required=False, allow_blank=True)
    output_text = serializers.CharField(required=False, allow_blank=True)
    output = serializers.CharField(required=False, allow_blank=True)

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        ret["input_context"] = (
            ret.get("input_context") or ret.get("context") or ret.get("query") or ""
        )
        ret["output_text"] = ret.get("output_text") or ret.get("output") or ""
        return ret


class DPOCurationSerializer(serializers.Serializer):
    feedback_id = serializers.IntegerField()
    chosen_text = serializers.CharField()


class AIDebateSerializer(serializers.Serializer):
    media_title = serializers.CharField()
    topic = serializers.CharField()


class CounterfactualSerializer(serializers.Serializer):
    what_if = serializers.CharField()
    actual_context = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )


class CoveOracleSerializer(serializers.Serializer):
    question = serializers.CharField()
    media_type = serializers.CharField(required=False, default="anime")


class CFRStrategySerializer(serializers.Serializer):
    questions = serializers.ListField(child=serializers.CharField(), required=False)
    iterations = serializers.IntegerField(
        required=False, default=100, min_value=1, max_value=1000
    )


class VoiceProfileSerializer(serializers.ModelSerializer):
    sample_url = serializers.ReadOnlyField()

    class Meta:
        model = VoiceProfile
        fields = [
            "id",
            "name",
            "language",
            "origin",
            "definition",
            "roles",
            "impact",
            "origin_detail",
            "sample_url",
            "created_at",
            "updated_at",
        ]

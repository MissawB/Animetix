from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html

from animetix.containers import get_container
from animetix.models import AIFeedback, AIREvalResult, AISafetyEvent, GoldDatasetEntry


@admin.register(GoldDatasetEntry)
class GoldDatasetEntryAdmin(admin.ModelAdmin):
    change_list_template = "admin/golddatasetentry_changelist.html"
    list_display = (
        "id",
        "entry_type",
        "instruction_preview",
        "is_validated",
        "ai_validation_score_display",
        "confidence_score_display",
        "is_safe_display",
        "created_at",
        "validation_status_display",
    )
    list_editable = ("is_validated",)
    list_filter = ("is_validated", "entry_type", "is_safe", "created_at")
    search_fields = ("instruction", "context", "response", "ai_critique")
    readonly_fields = (
        "created_at",
        "source_feedback",
        "ai_validation_score",
        "confidence_score",
        "is_safe",
    )
    actions = ["validate_selected", "invalidate_selected", "promote_selected_entries"]

    fieldsets = (
        (
            "Données Synthétiques",
            {
                "fields": (
                    "entry_type",
                    "instruction",
                    "context",
                    "response",
                    "metadata",
                )
            },
        ),
        (
            "Validation IA (HITL Gate)",
            {
                "fields": (
                    "ai_validation_score",
                    "confidence_score",
                    "is_safe",
                    "ai_critique",
                ),
                "description": "Résultats de la validation croisée automatique.",
            },
        ),
        (
            "Statut Humain",
            {"fields": ("is_validated", "source_feedback", "created_at")},
        ),
    )

    def instruction_preview(self, obj):
        return (
            obj.instruction[:80] + "..."
            if len(obj.instruction) > 80
            else obj.instruction
        )

    instruction_preview.short_description = "Instruction"

    def ai_validation_score_display(self, obj):
        color = (
            "green"
            if obj.ai_validation_score >= 0.7
            else "orange" if obj.ai_validation_score >= 0.4 else "red"
        )
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color,
            obj.ai_validation_score,
        )

    ai_validation_score_display.short_description = "Score IA"
    ai_validation_score_display.admin_order_field = "ai_validation_score"

    def confidence_score_display(self, obj):
        color = (
            "green"
            if obj.confidence_score >= 0.7
            else "orange" if obj.confidence_score >= 0.4 else "red"
        )
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color,
            obj.confidence_score,
        )

    confidence_score_display.short_description = "Confiance XAI"
    confidence_score_display.admin_order_field = "confidence_score"

    def is_safe_display(self, obj):
        if obj.is_safe:
            return format_html('<span style="color: green;">✔ Safe</span>')
        return format_html(
            '<span style="color: red; font-weight: bold;">✖ UNSAFE</span>'
        )

    is_safe_display.short_description = "Sécurité"

    def validation_status_display(self, obj):
        from django.utils.safestring import mark_safe  # noqa: E402

        if obj.is_validated:
            return mark_safe(
                '<span style="color: green; font-weight: bold;">✔ Validé</span>'
            )  # nosec B308
        return mark_safe(
            '<span style="color: orange; font-weight: bold;">⏳ En attente</span>'
        )  # nosec B308

    validation_status_display.short_description = "Statut"

    def validate_selected(self, request, queryset):
        rows_updated = queryset.update(is_validated=True)
        if rows_updated == 1:
            message_bit = "1 entrée a été validée."
        else:
            message_bit = f"{rows_updated} entrées ont été validées."
        self.message_user(request, f"Succès : {message_bit}", messages.SUCCESS)

    validate_selected.short_description = "Valider les entrées sélectionnées"

    def invalidate_selected(self, request, queryset):
        rows_updated = queryset.update(is_validated=False)
        if rows_updated == 1:
            message_bit = "1 entrée a été invalidée."
        else:
            message_bit = f"{rows_updated} entrées ont été invalidées."
        self.message_user(request, f"Succès : {message_bit}", messages.SUCCESS)

    invalidate_selected.short_description = "Invalider les entrées sélectionnées"

    def promote_selected_entries(self, request, queryset):
        validated_subset = queryset.filter(is_validated=True)
        if not validated_subset.exists():
            self.message_user(
                request,
                "Erreur : Aucune des entrées sélectionnées n'est validée (is_validated=True). Seules les entrées validées peuvent être promues.",
                messages.WARNING,
            )
            return

        container = get_container()
        promotion_service = container.synthetic_promotion_service()

        try:
            stats = promotion_service.promote_validated_entries()
            count = stats.get("promoted", 0)
            details = stats.get("details", {})
            self.message_user(
                request,
                f"Promotion réussie de {count} entrées. Détails: {details}",
                messages.SUCCESS,
            )
        except Exception as e:
            self.message_user(
                request, f"Erreur lors de la promotion : {str(e)}", messages.ERROR
            )

    promote_selected_entries.short_description = (
        "Promouvoir les entrées sélectionnées validées"
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "promote/",
                self.admin_site.admin_view(self.promote_validated_view),
                name="animetix_golddatasetentry_promote",
            ),
        ]
        return custom_urls + urls

    def promote_validated_view(self, request):
        container = get_container()
        promotion_service = container.synthetic_promotion_service()
        try:
            stats = promotion_service.promote_validated_entries()
            count = stats.get("promoted", 0)
            details = stats.get("details", {})
            msg = f"Succès : {count} entrées validées ont été promues et exportées. Détails : {details}"
            self.message_user(request, msg, messages.SUCCESS)
        except Exception as e:
            self.message_user(
                request,
                f"Erreur lors de la promotion globale : {str(e)}",
                messages.ERROR,
            )
        return redirect("../")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # Calcul des statistiques interactives
        extra_context["stats"] = {
            "pending_qa": GoldDatasetEntry.objects.filter(
                is_validated=False, entry_type="QA"
            ).count(),
            "pending_multiverse": GoldDatasetEntry.objects.filter(
                is_validated=False, entry_type="MULTIVERSE"
            ).count(),
            "pending_distillation": GoldDatasetEntry.objects.filter(
                is_validated=False, entry_type="DISTILLATION"
            ).count(),
            "pending_other": GoldDatasetEntry.objects.filter(
                is_validated=False, entry_type="OTHER"
            ).count(),
            "total_validated": GoldDatasetEntry.objects.filter(
                is_validated=True
            ).count(),
        }
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(AIFeedback)
class AIFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "feedback_type",
        "is_positive",
        "created_at",
        "input_context_truncated",
    )
    list_filter = ("is_positive", "feedback_type", "created_at")
    search_fields = ("input_context", "output_text", "user__username")
    readonly_fields = ("created_at",)

    def input_context_truncated(self, obj):
        return (
            obj.input_context[:100] + "..."
            if len(obj.input_context) > 100
            else obj.input_context
        )

    input_context_truncated.short_description = "Prompt/Contexte"


@admin.register(AISafetyEvent)
class AISafetyEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_type",
        "action",
        "detected_categories",
        "created_at",
        "user",
    )
    list_filter = ("event_type", "action", "created_at")
    search_fields = ("input_text", "output_text", "reasoning", "user__username")
    readonly_fields = ("created_at",)


@admin.register(AIREvalResult)
class AIREvalResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "game_mode",
        "faithfulness",
        "relevancy",
        "precision",
        "hallucination_detected",
        "created_at",
    )
    list_filter = ("game_mode", "hallucination_detected", "created_at")
    search_fields = ("input_context", "output_text")
    readonly_fields = ("created_at",)

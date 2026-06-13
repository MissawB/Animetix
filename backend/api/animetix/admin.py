from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html
from animetix.containers import get_container
from animetix.models import GoldDatasetEntry, AIFeedback, AISafetyEvent, AIREvalResult

@admin.register(GoldDatasetEntry)
class GoldDatasetEntryAdmin(admin.ModelAdmin):
    change_list_template = "admin/golddatasetentry_changelist.html"
    list_display = (
        'id', 
        'entry_type', 
        'instruction_preview', 
        'context_preview', 
        'is_validated', 
        'created_at',
        'validation_status_display'
    )
    list_editable = ('is_validated',)
    list_filter = ('is_validated', 'entry_type', 'created_at')
    search_fields = ('instruction', 'context', 'response')
    readonly_fields = ('created_at', 'source_feedback')
    actions = ['validate_selected', 'invalidate_selected', 'promote_selected_entries']

    def instruction_preview(self, obj):
        return obj.instruction[:80] + "..." if len(obj.instruction) > 80 else obj.instruction
    instruction_preview.short_description = "Instruction"

    def context_preview(self, obj):
        return obj.context[:80] + "..." if len(obj.context) > 80 else obj.context
    context_preview.short_description = "Contexte"

    def validation_status_display(self, obj):
        from django.utils.safestring import mark_safe
        if obj.is_validated:
            return mark_safe('<span style="color: green; font-weight: bold;">✔ Validé</span>')
        return mark_safe('<span style="color: orange; font-weight: bold;">⏳ En attente</span>')
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
            self.message_user(request, "Erreur : Aucune des entrées sélectionnées n'est validée (is_validated=True). Seules les entrées validées peuvent être promues.", messages.WARNING)
            return

        container = get_container()
        promotion_service = container.synthetic_promotion_service()
        
        try:
            stats = promotion_service.promote_validated_entries()
            count = stats.get("promoted", 0)
            details = stats.get("details", {})
            self.message_user(request, f"Promotion réussie de {count} entrées. Détails: {details}", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Erreur lors de la promotion : {str(e)}", messages.ERROR)
    promote_selected_entries.short_description = "Promouvoir les entrées sélectionnées validées"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('promote/', self.admin_site.admin_view(self.promote_validated_view), name='animetix_golddatasetentry_promote'),
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
            self.message_user(request, f"Erreur lors de la promotion globale : {str(e)}", messages.ERROR)
        return redirect("../")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # Calcul des statistiques interactives
        extra_context['stats'] = {
            'pending_qa': GoldDatasetEntry.objects.filter(is_validated=False, entry_type='QA').count(),
            'pending_multiverse': GoldDatasetEntry.objects.filter(is_validated=False, entry_type='MULTIVERSE').count(),
            'pending_distillation': GoldDatasetEntry.objects.filter(is_validated=False, entry_type='DISTILLATION').count(),
            'pending_other': GoldDatasetEntry.objects.filter(is_validated=False, entry_type='OTHER').count(),
            'total_validated': GoldDatasetEntry.objects.filter(is_validated=True).count(),
        }
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(AIFeedback)
class AIFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'feedback_type', 'is_positive', 'created_at', 'input_context_truncated')
    list_filter = ('is_positive', 'feedback_type', 'created_at')
    search_fields = ('input_context', 'output_text', 'user__username')
    readonly_fields = ('created_at',)

    def input_context_truncated(self, obj):
        return obj.input_context[:100] + "..." if len(obj.input_context) > 100 else obj.input_context
    input_context_truncated.short_description = "Prompt/Contexte"


@admin.register(AISafetyEvent)
class AISafetyEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_type', 'action', 'detected_categories', 'created_at', 'user')
    list_filter = ('event_type', 'action', 'created_at')
    search_fields = ('input_text', 'output_text', 'reasoning', 'user__username')
    readonly_fields = ('created_at',)


@admin.register(AIREvalResult)
class AIREvalResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'game_mode', 'faithfulness', 'relevancy', 'precision', 'hallucination_detected', 'created_at')
    list_filter = ('game_mode', 'hallucination_detected', 'created_at')
    search_fields = ('input_context', 'output_text')
    readonly_fields = ('created_at',)

import os
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .common import animetix_service
from ..models import AIREvalResult, GoldDatasetEntry, AIFeedback

def health_check_view(request):
    status = animetix_service.get_status()
    return render(request, 'animetix/admin/health.html', {'status': status})

def ai_evaluation_dashboard(request):
    results = AIREvalResult.objects.all().order_by('-created_at')[:50]
    from django.db.models import Avg, Count
    stats = AIREvalResult.objects.aggregate(avg_faith=Avg('faithfulness'), avg_rel=Avg('relevancy'), avg_prec=Avg('precision'), total=Count('id'))
    hallucinations = AIREvalResult.objects.filter(hallucination_detected=True).count()
    return render(request, 'animetix/admin/ai_eval.html', {'results': results, 'stats': stats, 'hallucination_count': hallucinations})

def latent_space_view(request):
    media, vibe_type = request.GET.get('media', 'anime').lower(), request.GET.get('type', 'thematic').lower()
    file_map = {'anime': {'thematic': 'latent_space_anime_thematic.json', 'visual': 'latent_space_anime_visual_vibe.json', 'scenario': 'latent_space_anime_plot.json'}, 'manga': {'thematic': 'latent_space_manga_thematic.json', 'visual': 'latent_space_manga_visual_vibe.json', 'scenario': 'latent_space_manga_plot.json'}, 'character': {'thematic': 'latent_space_character_vibe.json', 'visual': 'latent_space_character_visual_vibe.json'}}
    filename = file_map.get(media, file_map['anime']).get(vibe_type, 'latent_space_anime_thematic.json')
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir))) # Adjusting for deeper path
    data_path = os.path.join(project_root, 'data', 'artifacts', filename)
    if not os.path.exists(data_path): data_path = os.path.join(project_root, 'data', 'artifacts', 'latent_space_3d.json')
    latent_data = "[]"
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f: latent_data = f.read()
    return render(request, 'animetix/mlops/latent_viz.html', {'latent_data_json': latent_data, 'current_media': media, 'current_type': vibe_type})

def submit_ai_feedback(request):
    if request.method == 'POST':
        is_pos = request.POST.get('is_positive') == 'true'
        f_type = request.POST.get('type', 'general')
        
        # Extract context with fallback (Priority: input_context -> context -> query)
        context = request.POST.get('input_context') or request.POST.get('context') or request.POST.get('query', '')
        
        # Extract output with fallback (Priority: output_text -> output)
        output = request.POST.get('output_text') or request.POST.get('output', '')
        
        AIFeedback.objects.create(
            user=request.user if request.user.is_authenticated else None,
            feedback_type=f_type,
            input_context=context,
            output_text=output,
            is_positive=is_pos
        )
        return render(request, 'animetix/partials/feedback_thanks.html')
    return redirect('index')

@staff_member_required
def gold_curation_view(request):
    positive_feedbacks = AIFeedback.objects.filter(is_positive=True).exclude(golddatasetentry__isnull=False)
    for fb in positive_feedbacks: GoldDatasetEntry.objects.create(context=fb.input_context, instruction="Réponds à la question de l'utilisateur sur l'anime/manga.", response=fb.output_text, source_feedback=fb)
    entries, validated_count = GoldDatasetEntry.objects.filter(is_validated=False).order_by('-created_at'), GoldDatasetEntry.objects.filter(is_validated=True).count()
    return render(request, 'animetix/admin/gold_curation.html', {'entries': entries, 'validated_count': validated_count})

@staff_member_required
def validate_gold_entry(request, entry_id):
    try:
        entry = GoldDatasetEntry.objects.get(id=entry_id)
        entry.is_validated = True; entry.save(); return HttpResponse(status=204)
    except GoldDatasetEntry.DoesNotExist: return HttpResponse(status=404)

@staff_member_required
def reject_gold_entry(request, entry_id):
    try: GoldDatasetEntry.objects.get(id=entry_id).delete(); return HttpResponse(status=204)
    except GoldDatasetEntry.DoesNotExist: return HttpResponse(status=404)

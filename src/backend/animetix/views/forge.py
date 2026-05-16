import json
import random
from django.shortcuts import render, redirect
from celery import chain
from .common import animetix_service, logger
from ..utils import get_current_mode
from ..services import DIFFICULTY_SETTINGS
from ..presenters import ArchetypistPresenter
from ..models import CreativeFusion
from ..tasks import generate_fusion_scenario_task, generate_fusion_image_task

def archetypist_view(request):
    media_type, difficulty, data = get_current_mode(request), request.session.get('difficulty', 'Normal'), animetix_service.load_data(get_current_mode(request))
    if not data: logger.error(f"❌ Archetypist Error: Data for {media_type} not loaded"); return redirect('index')
    cross_options = ArchetypistPresenter.get_cross_media_options(media_type)
    
    if (request.method == 'POST' and request.POST.get('title_A')) or request.GET.get('replay') == '1':
        title_A, title_B = request.POST.get('title_A'), request.POST.get('title_B')
        media_A, media_B = request.POST.get('media_type_A', media_type), request.POST.get('media_type_B', media_type)
        
        # New Parameters
        chaos_level = int(request.POST.get('chaos_level', 50))
        universe_balance = int(request.POST.get('universe_balance', 50))
        art_style = request.POST.get('art_style', 'Cyberpunk')
        parent_id = request.POST.get('parent_id')
        
        data_A, data_B = animetix_service.load_data(media_A) if media_A != media_type else data, animetix_service.load_data(media_B) if media_B != media_type else data
        if not data_A or not data_B: return redirect('index')
        
        valid_A, valid_B = [t for t in data_A.get('titles', []) if t in data_A.get('title_to_full_data', {})], [t for t in data_B.get('titles', []) if t in data_B.get('title_to_full_data', {})]
        if not valid_A or not valid_B: return redirect('index')
        
        t1, t2 = title_A if title_A else random.choice(valid_A[:500]), title_B if title_B else random.choice(valid_B[:500])
        item1, item2 = data_A['title_to_full_data'].get(t1), data_B['title_to_full_data'].get(t2)
        if not item1 or not item2: return redirect('index')
        
        request.session['temp_item_A'], request.session['temp_item_B'] = item1, item2
        
        # Determine parent
        parent_fusion = None
        if parent_id:
            try:
                parent_fusion = CreativeFusion.objects.get(id=parent_id)
            except (CreativeFusion.DoesNotExist, ValueError):
                pass
        
        # Save placeholder fusion
        fusion = CreativeFusion.objects.create(
            title_a=t1, title_b=t2, media_type_a=media_A, media_type_b=media_B,
            chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style,
            creator=request.user if request.user.is_authenticated else None,
            parent=parent_fusion,
            scenario_text="Génération en cours..."
        )
        
        task = chain(
            generate_fusion_scenario_task.s(media_type, item1, item2, request.session.get('language', 'Français'), chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style), 
            generate_fusion_image_task.s(item1, item2, art_style=art_style)
        ).delay()
        
        context = {'task_id': task.id, 'media_type': media_type, 'item_A': item1, 'item_B': item2, 'show_titles': True, 'fusion_id': fusion.id}
        if request.headers.get('HX-Request'): 
            return render(request, 'animetix/archetypist/archetypist_loading_fragment.html', context)
        return render(request, 'animetix/archetypist/archetypist.html', context)
    media_settings = DIFFICULTY_SETTINGS.get(media_type, DIFFICULTY_SETTINGS["Anime"])
    # ... (rest of view)

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def like_fusion(request, fusion_id):
    """Handle liking/unliking a fusion via HTMX."""
    try:
        fusion = CreativeFusion.objects.get(id=fusion_id)
        if request.user in fusion.likes.all():
            fusion.likes.remove(request.user)
            liked = False
        else:
            fusion.likes.add(request.user)
            liked = True
        
        count = fusion.likes.count()
        icon = "bi-heart-fill text-rose-500" if liked else "bi-heart"
        # Return simple HTML fragment for HTMX to swap the button content
        return HttpResponse(f'<i class="bi {icon} group-hover:scale-125 transition"></i> <span class="manga-font text-[10px]">{count} LIKES</span>')
    except (CreativeFusion.DoesNotExist, ValueError):
        return HttpResponse("Error", status=404)

    rank_limit = media_settings.get(difficulty, 300)
    full_pool = data.get('db', [])
    if rank_limit is not None:
        if data.get('lookup'):
            limit_titles = [(t.get('title') or t.get('name')) for t in data['lookup'][:rank_limit]]
            pool = [item for item in full_pool if (item.get('title') or item.get('name')) in limit_titles]
        else: pool = full_pool[:rank_limit]
    else: pool = full_pool
    example_covers, display_items = ArchetypistPresenter.get_example_covers(pool), ArchetypistPresenter.build_forge_items(data)
    cross_data = {}
    for opt in cross_options:
        d_opt = animetix_service.load_data(opt['type'])
        if d_opt: cross_data[opt['type']] = ArchetypistPresenter.build_forge_items(d_opt, limit=300)
    return render(request, 'animetix/archetypist/archetypist_form.html', {'items_json': json.dumps(display_items), 'media_type': media_type, 'example_covers': example_covers, 'cross_options': cross_options, 'cross_data_json': json.dumps(cross_data)})

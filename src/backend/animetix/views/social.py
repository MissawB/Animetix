from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from ..models import Profile, Achievement, UserAchievement, Friendship, CreativeFusion, Notification

@login_required
def notifications_list_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    return render(request, 'animetix/social/notifications.html', {'notifications': notifications})

@login_required
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})

@login_required
def toggle_collection(request, fusion_id):
    """Handle adding/removing a fusion from the user's collection via HTMX."""
    try:
        fusion = CreativeFusion.objects.get(id=fusion_id)
        profile = request.user.profile
        
        if fusion in profile.collected_fusions.all():
            profile.collected_fusions.remove(fusion)
            collected = False
        else:
            profile.collected_fusions.add(fusion)
            collected = True
            
        icon = "bi-bookmark-star-fill text-amber-400" if collected else "bi-bookmark-star"
        text = "DANS LA COLLECTION" if collected else "COLLECTIONNER"
        
        return HttpResponse(f'''
            <button hx-post="/social/collection/toggle/{fusion.id}/" hx-swap="outerHTML" 
                    class="bg-white text-black rounded-full px-4 py-2 manga-font text-[10px] hover:scale-105 transition-all flex items-center justify-center gap-2 w-full">
                <i class="bi {icon} text-lg"></i> {text}
            </button>
        ''')
    except (CreativeFusion.DoesNotExist, ValueError):
        return HttpResponse("Error", status=404)

@login_required
def my_collection(request):
    """View to display the user's collected fusions."""
    collected_fusions = request.user.profile.collected_fusions.all().order_by('-created_at')
    return render(request, 'animetix/social/collection.html', {
        'fusions': collected_fusions
    })

def leaderboard_view(request):
    top_profiles = Profile.objects.select_related('user').order_by('-ranked_points')[:20]
    return render(request, 'animetix/leaderboard.html', {'top_profiles': top_profiles})

def achievements_view(request):
    all_ach = Achievement.objects.all(); unlocked = UserAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True) if request.user.is_authenticated else []
    return render(request, 'animetix/achievements.html', {'all_achievements': all_ach, 'unlocked_ids': list(unlocked)})

def profile_view(request, username):
    user = User.objects.get(username=username)
    is_following = False
    if request.user.is_authenticated:
        is_following = Friendship.objects.filter(from_user=request.user, to_user=user).exists()
    achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
    return render(request, 'animetix/social/profile.html', {'profile_user': user, 'is_following': is_following, 'unlocked_achievements': achievements})

@login_required
def social_dashboard(request):
    following = request.user.following.all().select_related('to_user__profile')
    followers = request.user.followers.all().select_related('from_user__profile')
    return render(request, 'animetix/social/dashboard.html', {'following': following, 'followers': followers})

@login_required
def toggle_follow(request, user_id):
    target_user = User.objects.get(id=user_id)
    if target_user == request.user: return HttpResponse(status=400)
    friendship, created = Friendship.objects.get_or_create(from_user=request.user, to_user=target_user)
    if not created: 
        friendship.delete()
        is_following = False
    else: 
        is_following = True
        from ..services import send_notification
        send_notification(
            user=target_user,
            title="Nouveau Follower !",
            message=f"{request.user.username} vient de commencer à vous suivre. Préparez vos prochains défis !",
            notification_type='social',
            link=f"/social/profile/{request.user.username}/"
        )
    if request.headers.get('HX-Request'):
        return render(request, 'animetix/social/follow_button_fragment.html', {'target_user': target_user, 'is_following': is_following})
    return redirect('profile_view', username=target_user.username)

def follow_user(request, user_id):
    if not request.user.is_authenticated: return redirect('login')
    to_user = User.objects.get(id=user_id)
    if to_user != request.user: Friendship.objects.get_or_create(from_user=request.user, to_user=to_user)
    return redirect(request.META.get('HTTP_REFERER', 'index'))

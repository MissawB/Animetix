import json
import logging
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from ..containers import get_container
from core.domain.entities.donation import Donation as DomainDonation

logger = logging.getLogger("animetix.donation")

def transparency_dashboard(request):
    """Vue du tableau de bord de transparence."""
    container = get_container()
    health_service = container.health_dashboard_service
    stats = health_service.get_health_stats()
    
    return render(request, 'animetix/transparency.html', {
        'stats': stats,
        'title': "Transparence & Santé du Projet"
    })

@csrf_exempt
def donation_webhook(request):
    """
    Webhook pour recevoir les notifications de dons (ex: Ko-fi).
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        # Exemple pour Ko-fi
        data = json.loads(request.POST.get('data', '{}'))
        if not data:
            # Essayer de lire le body brut si ce n'est pas dans un champ 'data'
            data = json.loads(request.body)

        amount = float(data.get('amount', 0))
        currency = data.get('currency', 'USD')
        platform = "Ko-fi"
        transaction_id = data.get('message_id')
        email = data.get('email')
        
        # Trouver l'utilisateur par email si possible
        user = User.objects.filter(email=email).first()
        
        container = get_container()
        donation_port = container.health_dashboard_service.donation_port
        achievement_service = container.achievement_service
        
        domain_donation = DomainDonation(
            user_id=user.id if user else None,
            amount=amount,
            currency=currency,
            platform=platform,
            transaction_id=transaction_id,
            message=data.get('message', '')
        )
        
        donation_port.save(domain_donation)
        logger.info(f"Donation received: {amount} {currency} from {email}")
        
        # Débloquer les achievements si l'utilisateur est connu
        if user:
            achievement_service.unlock_by_code(user.id, 'donor_bronze')
            
            # Badge "Gardien" pour les gros dons (ex: > 50 USD)
            if amount >= 50:
                achievement_service.unlock_by_code(user.id, 'donor_gold')

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error processing donation webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

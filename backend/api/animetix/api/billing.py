from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from ..models import WalletTransaction, Profile
from animetix_project.logging_config import get_logger

logger = get_logger(__name__)

class PaymentRequired(APIException):
    status_code = 402
    default_detail = 'Fonds insuffisants. Veuillez recharger vos Berrix (Bx) dans la Power Station.'
    default_code = 'payment_required'

def deduct_berrix(user, amount: int, description: str):
    """
    Déduit des Berrix (Bx) du portefeuille de l'utilisateur de manière atomique.
    Lève une exception PaymentRequired (HTTP 402) si le solde est insuffisant.
    """

    if not user.is_authenticated:
        # Les invités pourraient avoir un budget temporaire basé sur l'IP, mais pour l'instant on force l'auth.
        raise PaymentRequired("Vous devez être connecté pour utiliser cette fonctionnalité.")

    with transaction.atomic():
        # Select for update to prevent race conditions
        profile = Profile.objects.select_for_update().get(user=user)
        
        if profile.wallet_balance < amount:
            raise PaymentRequired()
            
        profile.wallet_balance -= amount
        profile.save()
        
        WalletTransaction.objects.create(
            user=user,
            amount=-amount,
            transaction_type='ai_usage',
            description=description
        )

class WalletMineView(APIView):
    """
    Endpoint pour le minage passif de Berrix (Bx).
    Crédite le portefeuille de l'utilisateur s'il a passé assez de temps sur le site.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        cache_key = f"last_mine_{user.id}"
        
        # Anti-spam: Vérifier le délai de 3 minutes (180 secondes)
        last_mine = cache.get(cache_key)
        if last_mine:
            return Response({
                "error": "Cooldown active",
                "message": "Le minage neuronal prend du temps. Attendez encore un peu."
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Augmentation pour marge minimale: 20 Bx par session de 3 min
        amount = 20 
        
        try:
            with transaction.atomic():
                profile = user.profile
                profile.wallet_balance += amount
                profile.save()
                
                WalletTransaction.objects.create(
                    user=user,
                    amount=amount,
                    transaction_type='ad_passive',
                    description="Minage passif (Berrix)"
                )
            
            # Poser le verrou de cooldown
            cache.set(cache_key, True, timeout=175) # 175s pour être un peu plus souple que le setInterval frontend
            
            return Response({
                "status": "success",
                "new_balance": profile.wallet_balance,
                "earned": amount
            })
        except Exception as e:
            logger.error(f"WalletMine Error: {e}")
            return Response({"error": "Failed to credit Berrix"}, status=500)

class WalletWatchAdView(APIView):
    """
    Endpoint pour la recharge active via Reward Ads (Berrix).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        # Augmentation pour marge minimale: 250 Bx par vidéo (Généreux +++)
        amount = 250 
        
        try:
            with transaction.atomic():
                profile = user.profile
                profile.wallet_balance += amount
                profile.save()
                
                WalletTransaction.objects.create(
                    user=user,
                    amount=amount,
                    transaction_type='ad_active',
                    description="Recharge active (Berrix)"
                )
            
            return Response({
                "status": "success",
                "new_balance": profile.wallet_balance,
                "earned": amount
            })
        except Exception as e:
            logger.error(f"WalletWatchAd Error: {e}")
            return Response({"error": "Failed to credit Berrix"}, status=500)

class WalletBalanceView(APIView):
    """
    Récupère le solde actuel et l'historique récent des transactions.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        transactions = WalletTransaction.objects.filter(user=user).order_by('-created_at')[:10]
        
        history = [{
            "amount": t.amount,
            "type": t.transaction_type,
            "description": t.description,
            "date": t.created_at
        } for t in transactions]
        
        return Response({
            "balance": user.profile.wallet_balance,
            "history": history
        })

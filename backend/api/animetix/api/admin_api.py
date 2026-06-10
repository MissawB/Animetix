from rest_framework import viewsets, permissions, response, status, decorators
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from ..models import DataCurationTicket, AITokenUsage, AdEvent
from ..serializers import DataCurationTicketSerializer, UserAdminSerializer
from django.contrib.auth.models import User

class UserManagementViewSet(viewsets.ModelViewSet):
    """Gestion des comptes utilisateurs pour les administrateurs."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserAdminSerializer
    permission_classes = [permissions.IsAdminUser]

    @decorators.action(detail=True, methods=['post'])
    def toggle_staff(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return response.Response({'error': 'Vous ne pouvez pas modifier votre propre statut.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_staff = not user.is_staff
        user.save()
        return response.Response({'status': 'updated', 'is_staff': user.is_staff})

    @decorators.action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return response.Response({'error': 'Vous ne pouvez pas vous désactiver vous-même.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = not user.is_active
        user.save()
        return response.Response({'status': 'updated', 'is_active': user.is_active})

class DataCurationTicketViewSet(viewsets.ModelViewSet):
    """Dashboard de curation pour les administrateurs."""
    queryset = DataCurationTicket.objects.all().order_by('-created_at')
    serializer_class = DataCurationTicketSerializer
    permission_classes = [permissions.IsAdminUser]

    @decorators.action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        ticket = self.get_object()
        ticket.is_resolved = True
        ticket.save()
        return response.Response({'status': 'resolved'})

    @decorators.action(detail=False, methods=['get'])
    def stats(self, request):
        total = DataCurationTicket.objects.count()
        pending = DataCurationTicket.objects.filter(is_resolved=False).count()
        resolved = total - pending
        
        return response.Response({
            "total_tickets": total,
            "pending_tickets": pending,
            "resolved_tickets": resolved,
            "health_score": round((resolved / total * 100), 1) if total > 0 else 100
        })

class TTCMonitoringAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        today = timezone.now() - timedelta(hours=24)
        qs = AITokenUsage.objects.filter(created_at__gte=today, allocated_budget__gt=0)
        
        total_allocated = qs.aggregate(Sum('allocated_budget'))['allocated_budget__sum'] or 0
        total_consumed = qs.aggregate(Sum('total_tokens'))['total_tokens__sum'] or 0
        
        recent_logs = qs.order_by('-created_at')[:50]
        
        return response.Response({
            "summary": {
                "total_allocated": total_allocated,
                "total_consumed": total_consumed,
                "efficiency": round((total_consumed / total_allocated * 100), 1) if total_allocated > 0 else 100
            },
            "logs": [
                {
                    "id": l.id,
                    "engine": l.engine,
                    "allocated": l.allocated_budget,
                    "consumed": l.total_tokens,
                    "timestamp": l.created_at
                } for l in recent_logs
            ]
        })

class AdEventLoggingAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        event_type = request.data.get("event_type")
        ad_type = request.data.get("ad_type")
        
        valid_events = dict(AdEvent.EVENT_TYPES)
        valid_ads = dict(AdEvent.AD_TYPES)
        
        if event_type not in valid_events or ad_type not in valid_ads:
            return response.Response({"error": "Invalid event_type or ad_type"}, status=status.HTTP_400_BAD_REQUEST)
            
        event = AdEvent.objects.create(
            event_type=event_type,
            ad_type=ad_type
        )
        return response.Response({"status": "logged", "id": event.id}, status=status.HTTP_201_CREATED)

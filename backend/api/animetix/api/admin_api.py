from rest_framework import viewsets, permissions, response, status, decorators
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from ..models import DataCurationTicket, AITokenUsage
from ..serializers import DataCurationTicketSerializer

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

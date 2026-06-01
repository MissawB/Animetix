from rest_framework import viewsets, permissions, response, status, decorators
from ..models import DataCurationTicket
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

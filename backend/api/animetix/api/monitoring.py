from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.management import call_command
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

@method_decorator(staff_member_required, name='dispatch')
class PipelineControlView(APIView):
    def post(self, request, action):
        if action == 'run_scraper':
            try:
                call_command('run_scrapers')
                return Response({'status': 'Scrapers triggered'})
            except Exception as e:
                return Response({'error': str(e)}, status=500)
        elif action == 'sync_neo4j':
            try:
                call_command('sync_catalog')
                return Response({'status': 'Neo4j sync triggered'})
            except Exception as e:
                return Response({'error': str(e)}, status=500)
        return Response({'error': 'Invalid action'}, status=400)

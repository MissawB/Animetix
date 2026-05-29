import os
import sys

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')

django_asgi_app = get_asgi_application()

import animetix.routing

# Python 3.12+ Compatibility: Handle event loop policy on Windows
if sys.platform == 'win32':
    import asyncio
    try:
        policy = asyncio.WindowsProactorEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)
    except Exception:
        # Policy might already be set or not supported on this Windows version
        pass

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            animetix.routing.websocket_urlpatterns
        )
    ),
})

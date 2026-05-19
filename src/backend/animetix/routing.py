from django.urls import re_path
from .consumers import (
    UndercoverConsumer, 
    CodeMangaConsumer, 
    NotificationConsumer, 
    DuelConsumer
)

websocket_urlpatterns = [
    re_path(r'ws/undercover/(?P<room_code>\w+)/$', UndercoverConsumer.as_asgi()),
    re_path(r'ws/codemanga/(?P<room_code>\w+)/$', CodeMangaConsumer.as_asgi()),
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
    re_path(r'ws/duel/(?P<lobby_id>\w+)/$', DuelConsumer.as_asgi()),
]

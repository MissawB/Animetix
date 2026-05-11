from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/undercover/(?P<room_code>\w+)/$', consumers.UndercoverConsumer.as_asgi()),
    re_path(r'ws/codemanga/(?P<room_code>\w+)/$', consumers.CodeMangaConsumer.as_asgi()),
]

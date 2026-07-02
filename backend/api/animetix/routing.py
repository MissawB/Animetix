from django.urls import re_path

from .consumers import (
    ClubConsumer,
    CodeMangaConsumer,
    DuelConsumer,
    NotificationConsumer,
    QuizWhoConsumer,
    SpeechToSpeechLiveConsumer,
    UndercoverConsumer,
)

websocket_urlpatterns = [
    re_path(r"ws/undercover/(?P<room_code>\w+)/$", UndercoverConsumer.as_asgi()),
    re_path(r"ws/codemanga/(?P<room_code>\w+)/$", CodeMangaConsumer.as_asgi()),
    re_path(r"ws/quizwho/(?P<room_code>\w+)/$", QuizWhoConsumer.as_asgi()),
    re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
    re_path(r"ws/duel/(?P<lobby_id>\w+)/$", DuelConsumer.as_asgi()),
    re_path(r"ws/club/(?P<club_id>\d+)/$", ClubConsumer.as_asgi()),
    re_path(r"ws/labs/s2s/live/$", SpeechToSpeechLiveConsumer.as_asgi()),
]

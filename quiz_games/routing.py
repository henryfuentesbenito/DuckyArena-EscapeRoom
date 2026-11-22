from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/quiz/game/(?P<code>\w+)/$', consumers.GameRoomConsumer.as_asgi()),
]

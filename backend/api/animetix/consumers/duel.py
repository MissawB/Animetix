import json

from animetix_project.logging_config import get_logger
from asgiref.sync import sync_to_async
from core.domain.exceptions import GameLogicError
from django.core.cache import cache

from ..containers import get_container
from .base import BaseConsumer

logger = get_logger("animetix." + __name__)

# Le classement d'un catalogue face à un secret est cher UNE fois (index +
# comparaisons), gratuit ensuite : mis en cache par (media_type, secret_title),
# relu à chaque proposition -- une partie de duel calcule le sien une fois par
# salle, exactement comme le mode Classique calcule le sien une fois par partie
# (backend/api/animetix/api/games/classic.py). Même clé de cache : si un défi
# classique et un duel partagent (media_type, secret), le second à demander lit
# le calcul du premier.
PROXIMITY_CACHE_TIMEOUT = 60 * 60 * 24 * 7  # 7 jours


class DuelConsumer(BaseConsumer):
    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["lobby_id"]
        self.room_group_name = f"duel_{self.room_code}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        # Vérification de la salle en DB
        from ..models import DuelRoom  # noqa: E402

        try:
            self.duel = await sync_to_async(DuelRoom.objects.get)(
                room_code=self.room_code
            )
        except DuelRoom.DoesNotExist:
            await self.close()
            return

        # Sécurité : Vérifier que l'utilisateur est l'un des participants
        p1 = await sync_to_async(lambda: self.duel.player1)()
        p2 = await sync_to_async(lambda: self.duel.player2)()
        if self.user != p1 and self.user != p2:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.broadcast_state()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("type")

        if action == "guess":
            await self.handle_guess(data.get("guess"))

    async def handle_guess(self, guess):
        from ..models import DuelRoom  # noqa: E402

        duel = await sync_to_async(DuelRoom.objects.get)(room_code=self.room_code)

        if duel.is_finished:
            return

        # On charge les data pour la similarité
        container = get_container()
        data = await sync_to_async(container.core.catalog_service().load_data)(
            duel.media_type
        )
        secret = duel.secret_title

        # Vérification match direct
        secret_item = data["title_to_full_data"].get(secret)
        is_correct = await sync_to_async(
            container.core.game_service().check_title_match
        )(guess, secret_item)

        if is_correct:
            duel.is_finished = True
            duel.winner = self.user
            await sync_to_async(duel.save)()

            # Récompense
            profile = await sync_to_async(lambda: self.user.profile)()
            await sync_to_async(profile.add_win)(
                game_mode="duel", media_type=duel.media_type
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "send_msg",
                    "message": {
                        "type": "duel_finished",
                        "winner": self.user.username,
                        "secret": secret,
                    },
                },
            )
        else:
            # Score honnête : le percentile ProximityService (même moteur que le mode
            # Classique), pas le cosinus brut -- sur le vrai catalogue, deux oeuvres
            # SANS AUCUNE relation moyennent 0.583 de cosinus : un joueur qui propose
            # un titre sans rapport verrait ~58 %, lisant "tu chauffes" alors qu'il n'y
            # a rien. Le classement est cher (tout le catalogue) : mis en cache par
            # (media_type, secret_title), calculé une fois par salle et relu à chaque
            # proposition.
            proximity_service = container.core.proximity_service()
            cache_key = f"proximity_{duel.media_type}_{secret}"
            ranking = await sync_to_async(cache.get)(cache_key)
            try:
                if ranking is None:
                    ranking = await sync_to_async(proximity_service.rank)(
                        duel.media_type, secret
                    )
                    await sync_to_async(cache.set)(
                        cache_key, ranking, timeout=PROXIMITY_CACHE_TIMEOUT
                    )
                report = await sync_to_async(proximity_service.report)(
                    duel.media_type, secret, guess, ranking=ranking
                )
            except GameLogicError as e:
                # Aucun signal exploitable pour ce type de média (films, jeux,
                # acteurs aujourd'hui) : une panne de service connue, pas un bug.
                # Ne DOIT PAS faire planter la boucle websocket -- on prévient
                # seulement le joueur qui vient de proposer, pas toute la salle.
                logger.warning(
                    f"Duel: no proximity signal for {duel.media_type}/{secret}: {e}"
                )
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "error",
                            "message": "Proximity scoring unavailable for this media type.",
                        }
                    )
                )
                return

            # Le percentile seul, pas les "reasons" : le duel est une course entre
            # deux joueurs qui voient les scores de l'autre (opponent_guess est
            # diffusé à toute la salle) -- révéler ce qui rapproche donnerait à
            # l'adversaire une longueur d'avance gratuite. Le mode Classique, solo,
            # peut se permettre ce détail ; le duel s'en tient au nombre.
            score = report["percent"]

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "send_msg",
                    "message": {
                        "type": "opponent_guess",
                        "player": self.user.username,
                        "score": score,
                    },
                },
            )

    async def broadcast_state(self):
        from ..models import DuelRoom  # noqa: E402

        duel = await sync_to_async(DuelRoom.objects.get)(room_code=self.room_code)
        p1 = await sync_to_async(lambda: duel.player1.username)()
        p2 = await sync_to_async(
            lambda: duel.player2.username if duel.player2 else None
        )()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_msg",
                "message": {
                    "type": "duel_state",
                    "player1": p1,
                    "player2": p2,
                    "media_type": duel.media_type,
                    "is_finished": duel.is_finished,
                },
            },
        )

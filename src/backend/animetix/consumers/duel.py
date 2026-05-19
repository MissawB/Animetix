import json
from asgiref.sync import sync_to_async
from .base import BaseConsumer
from ..containers import get_container

class DuelConsumer(BaseConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['lobby_id']
        self.room_group_name = f'duel_{self.room_code}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        # Vérification de la salle en DB
        from ..models import DuelRoom
        try:
            self.duel = await sync_to_async(DuelRoom.objects.get)(room_code=self.room_code)
        except DuelRoom.DoesNotExist:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        await self.broadcast_state()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('type')

        if action == 'guess':
            await self.handle_guess(data.get('guess'))

    async def handle_guess(self, guess):
        from ..models import DuelRoom
        duel = await sync_to_async(DuelRoom.objects.get)(room_code=self.room_code)
        
        if duel.is_finished: return

        # On charge les data pour la similarité
        container = get_container()
        data = await sync_to_async(container.catalog_service.load_data)(duel.media_type)
        secret = duel.secret_title
        
        # Vérification match direct
        secret_item = data['title_to_full_data'].get(secret)
        is_correct = await sync_to_async(container.game_service.check_title_match)(guess, secret_item)
        
        if is_correct:
            duel.is_finished = True
            duel.winner = self.user
            await sync_to_async(duel.save)()
            
            # Récompense
            profile = await sync_to_async(lambda: self.user.profile)()
            await sync_to_async(profile.add_win)(game_mode='duel', media_type=duel.media_type)
            
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_msg',
                'message': {
                    'type': 'duel_finished',
                    'winner': self.user.username,
                    'secret': secret
                }
            })
        else:
            # Similarité pour feedback (facultatif mais fun en 1vs1)
            raw_sim = await sync_to_async(container.game_service.calculate_raw_similarity)(
                duel.media_type, secret, guess, data
            )
            score = round(raw_sim * 100, 1)

            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_msg',
                'message': {
                    'type': 'opponent_guess',
                    'player': self.user.username,
                    'score': score
                }
            })

    async def broadcast_state(self):
        from ..models import DuelRoom
        duel = await sync_to_async(DuelRoom.objects.get)(room_code=self.room_code)
        p1 = await sync_to_async(lambda: duel.player1.username)()
        p2 = await sync_to_async(lambda: duel.player2.username if duel.player2 else None)()
        
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'send_msg',
            'message': {
                'type': 'duel_state',
                'player1': p1,
                'player2': p2,
                'media_type': duel.media_type,
                'is_finished': duel.is_finished
            }
        })

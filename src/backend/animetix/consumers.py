import json
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .containers import get_container
from .services import DIFFICULTY_SETTINGS
from adapters.persistence.django_cache_state_adapter import DjangoCacheStateAdapter

state_adapter = DjangoCacheStateAdapter()


# --- 1. CONSUMER UNDERCOVER ---
class UndercoverConsumer(AsyncWebsocketConsumer):
    async def get_room(self):
        room = await state_adapter.get_state(f"undercover_room_{self.room_code}")
        return room

    async def save_room(self, room):
        await state_adapter.set_state(f"undercover_room_{self.room_code}", room, timeout=3600)

    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code'].upper()
        self.room_group_name = f'undercover_{self.room_code}'

        room = await self.get_room()
        if not room:
            room = {
                'host': self.channel_name, 'players': {}, 'state': 'lobby', 
                'messages': [], 'clue': '', 'media_type': 'Anime', 'difficulty': 'Normal', 'votes': {}
            }

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        
        room['players'][self.channel_name] = {
            'name': f'Player {len(room["players"]) + 1}',
            'role': None, 'word': None, 'image': None, 'is_host': (self.channel_name == room['host'])
        }
        
        await self.save_room(room)
        await self.accept()
        await self.broadcast_state()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        room = await self.get_room()
        if room and self.channel_name in room['players']:
            del room['players'][self.channel_name]
            if not room['players']: 
                await state_adapter.delete_state(f"undercover_room_{self.room_code}")
            elif room['host'] == self.channel_name:
                new_host = list(room['players'].keys())[0]
                room['host'] = new_host
                room['players'][new_host]['is_host'] = True
                await self.save_room(room)
            else:
                await self.save_room(room)
            await self.broadcast_state()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        room = await self.get_room()
        if not room: return

        if action == 'set_name':
            room['players'][self.channel_name]['name'] = data.get('name', '')[:15]
            await self.save_room(room)
            await self.broadcast_state()
        elif action == 'set_settings' and self.channel_name == room['host']:
            room['media_type'] = data.get('media_type', 'Anime')
            room['difficulty'] = data.get('difficulty', 'Normal')
            await self.save_room(room)
            await self.broadcast_state()
        elif action == 'chat':
            msg = {'user': room['players'][self.channel_name]['name'], 'text': data.get('message', '')[:100], 'is_system': False}
            room['messages'].append(msg)
            await self.save_room(room)
            await self.broadcast_chat(msg)
        elif action == 'start_game' and self.channel_name == room['host']:
            await self.start_game_logic(room)
        elif action == 'vote':
            room['votes'][self.channel_name] = data.get('voted_for')
            await self.save_room(room)
            await self.broadcast_state()
        elif action == 'reveal' and self.channel_name == room['host']:
            room['state'] = 'revealed'
            await self.save_room(room)
            await self.broadcast_state()
        elif action == 'back_to_lobby' and self.channel_name == room['host']:
            room['state'] = 'lobby'
            room['votes'], room['messages'] = {}, []
            for p in room['players'].values(): p['role'], p['word'], p['image'] = None, None, None
            await self.save_room(room)
            await self.broadcast_state()

    async def broadcast_chat(self, msg):
        await self.channel_layer.group_send(self.room_group_name, {'type': 'send_msg', 'message': {'type': 'chat_message', 'message': msg}})

    async def broadcast_state(self):
        room = await self.get_room()
        if not room: return
        players_list = [{'id': ch, 'name': p['name'], 'is_host': p['is_host'], 'has_voted': ch in room['votes']} for ch, p in room['players'].items()]
        await self.channel_layer.group_send(self.room_group_name, {'type': 'send_msg', 'message': {'type': 'room_state', 'state': room['state'], 'players': players_list, 'clue': room['clue'], 'messages': room['messages'], 'difficulty': room['difficulty'], 'media_type': room['media_type']}})
        if room['state'] in ['playing', 'revealed']:
            for ch, p in room['players'].items():
                await self.channel_layer.send(ch, {'type': 'send_msg', 'message': {'type': 'private_role', 'role': p['role'], 'word': p['word'], 'image': p['image']}})

    async def start_game_logic(self, room):
        container = get_container()
        game_data = await sync_to_async(container.game_service.start_undercover_game)(
            media_type=room['media_type'], difficulty=room['difficulty'],
            player_ids=list(room['players'].keys()), rank_limits=DIFFICULTY_SETTINGS
        )
        if not game_data: return
        
        clue = await sync_to_async(container.llm_service.generate_undercover_clue)(
            room['media_type'], game_data['civil_word'], game_data['undercover_word']
        ) or "Mystère..."
        
        for ch, p in room['players'].items():
            assignment = game_data['assignments'][ch]
            p['role'], p['word'], p['image'] = assignment['role'], assignment['word'], assignment['image']
        room['clue'], room['state'] = clue, 'playing'
        await self.save_room(room)
        await self.broadcast_state()


    async def send_msg(self, event): await self.send(text_data=json.dumps(event['message']))

# --- 2. CONSUMER CODEMANGA ---
class CodeMangaConsumer(AsyncWebsocketConsumer):
    async def get_room(self): return await state_adapter.get_state(f"codemanga_room_{self.room_code}")
    async def save_room(self, room): await state_adapter.set_state(f"codemanga_room_{self.room_code}", room, timeout=3600)
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code'].upper()
        self.room_group_name = f'codemanga_{self.room_code}'
        room = await self.get_room()
        if not room: room = {'host': self.channel_name, 'players': {}, 'state': 'lobby', 'grid': [], 'turn': 'blue', 'blue_score': 0, 'red_score': 0, 'winner': None}
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        room['players'][self.channel_name] = {'name': f'Fan #{random.randint(100, 999)}', 'team': None, 'role': None}
        await self.save_room(room)
        await self.accept()
        await self.broadcast_state()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action, room = data.get('action'), await self.get_room()
        if not room: return
        if action == 'set_player': room['players'][self.channel_name].update({'name': data.get('name', 'Anonyme'), 'team': data.get('team', 'blue'), 'role': data.get('role', 'operative')})
        elif action == 'start_game': 
            await self.generate_grid(room); room['state'] = 'playing'; await self.save_room(room)
            await self.channel_layer.group_send(self.room_group_name, {'type': 'send_msg', 'message': {'type': 'redirect', 'url': f'/codemanga/game/{self.room_code}/'}})
        elif action == 'click_card': await self.handle_card_click(room, data.get('index'))
        await self.save_room(room); await self.broadcast_state()

    async def generate_grid(self, room):
        data = await sync_to_async(get_container().catalog_service.load_data)('Anime')
        if not data: return
        selected = random.sample(list(data['db']), 25)
        roles = (['blue'] * 9) + (['red'] * 8) + (['neutral'] * 7) + (['assassin'] * 1); random.shuffle(roles)
        room['grid'] = [{'title': selected[i].get('title'), 'image': selected[i].get('image'), 'role': roles[i], 'revealed': False} for i in range(25)]
        room['blue_score'], room['red_score'], room['turn'], room['winner'] = 0, 0, 'blue', None


    async def handle_card_click(self, room, idx):
        if room['state'] != 'playing' or room['winner']: return
        card = room['grid'][idx]
        if card['revealed']: return
        card['revealed'] = True
        if card['role'] == 'assassin': room['winner'] = ('red' if room['turn'] == 'blue' else 'blue')
        elif card['role'] != room['turn']: room['turn'] = ('red' if room['turn'] == 'blue' else 'blue')
        room['blue_score'] = sum(1 for c in room['grid'] if c['role'] == 'blue' and c['revealed'])
        room['red_score'] = sum(1 for c in room['grid'] if c['role'] == 'red' and c['revealed'])
        if room['blue_score'] == 9: room['winner'] = 'blue'
        if room['red_score'] == 8: room['winner'] = 'red'

    async def broadcast_state(self):
        room = await self.get_room()
        if not room: return
        public_grid = [{'title': c['title'], 'image': c['image'], 'revealed': c['revealed'], 'role': (c['role'] if c['revealed'] else 'unknown')} for c in room['grid']]
        for ch, p in room['players'].items():
            grid_to_send = room['grid'] if p['role'] == 'spymaster' else public_grid
            await self.channel_layer.send(ch, {'type': 'send_msg', 'message': {'type': 'state', 'room': {
                'state': room['state'], 'grid': grid_to_send, 'turn': room['turn'], 'blue_score': room['blue_score'],
                'red_score': room['red_score'], 'winner': room['winner'], 'players': list(room['players'].values())
            }, 'my_role': p['role'], 'my_team': p['team']}})

    async def send_msg(self, event): await self.send(text_data=json.dumps(event['message']))

# --- 3. CONSUMER NOTIFICATIONS ---
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 1. Groupe Global (tous les utilisateurs connectés)
        await self.channel_layer.group_add("global_notifications", self.channel_name)
        
        # 2. Groupe Privé (uniquement pour l'utilisateur)
        if not self.scope["user"].is_anonymous:
            self.user_id = self.scope["user"].id
            self.group_name = f"user_notifications_{self.user_id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("global_notifications", self.channel_name)
        if hasattr(self, 'group_name'): 
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event): 
        await self.send(text_data=json.dumps(event["data"]))

# --- 4. CONSUMER DUELS (1vs1) ---
class DuelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['lobby_id']
        self.room_group_name = f'duel_{self.room_code}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        # Vérification de la salle en DB
        from .models import DuelRoom
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
        from .models import DuelRoom
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
        from .models import DuelRoom
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

    async def send_msg(self, event):
        await self.send(text_data=json.dumps(event['message']))

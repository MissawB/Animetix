import json
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .services import AnimetixService, LangChainService, DIFFICULTY_SETTINGS

animetix_service = AnimetixService()

# --- ETAT MEMOIRE DES SALONS ---
ROOMS_UNDERCOVER = {}
ROOMS_CODEMANGA = {}

# --- 1. CONSUMER UNDERCOVER ---
class UndercoverConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code'].upper()
        self.room_group_name = f'undercover_{self.room_code}'

        if self.room_code not in ROOMS_UNDERCOVER:
            ROOMS_UNDERCOVER[self.room_code] = {
                'host': self.channel_name, 'players': {}, 'state': 'lobby', 
                'messages': [], 'clue': '', 'media_type': 'Anime', 'difficulty': 'Normal', 'votes': {}
            }

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        ROOMS_UNDERCOVER[self.room_code]['players'][self.channel_name] = {
            'name': f'Player {len(ROOMS_UNDERCOVER[self.room_code]["players"]) + 1}',
            'role': None, 'word': None, 'image': None, 'is_host': (self.channel_name == ROOMS_UNDERCOVER[self.room_code]['host'])
        }
        await self.accept()
        await self.broadcast_state()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        room = ROOMS_UNDERCOVER.get(self.room_code)
        if room and self.channel_name in room['players']:
            del room['players'][self.channel_name]
            if not room['players']: 
                if self.room_code in ROOMS_UNDERCOVER: del ROOMS_UNDERCOVER[self.room_code]
            elif room['host'] == self.channel_name:
                new_host = list(room['players'].keys())[0]
                room['host'] = new_host
                room['players'][new_host]['is_host'] = True
            await self.broadcast_state()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        room = ROOMS_UNDERCOVER.get(self.room_code)
        if not room:
            return

        if action == 'set_name':
            room['players'][self.channel_name]['name'] = data.get('name', '')[:15]
            await self.broadcast_state()
        elif action == 'set_settings' and self.channel_name == room['host']:
            room['media_type'] = data.get('media_type', 'Anime')
            room['difficulty'] = data.get('difficulty', 'Normal')
            await self.broadcast_state()
        elif action == 'chat':
            msg = {'user': room['players'][self.channel_name]['name'], 'text': data.get('message', '')[:100], 'is_system': False}
            room['messages'].append(msg)
            await self.broadcast_chat(msg)
        elif action == 'start_game' and self.channel_name == room['host']:
            await self.start_game_logic(room)
        elif action == 'vote':
            room['votes'][self.channel_name] = data.get('voted_for')
            await self.broadcast_state()
        elif action == 'reveal' and self.channel_name == room['host']:
            room['state'] = 'revealed'
            await self.broadcast_state()
        elif action == 'back_to_lobby' and self.channel_name == room['host']:
            room['state'] = 'lobby'
            room['votes'], room['messages'] = {}, []
            for p in room['players'].values(): p['role'], p['word'], p['image'] = None, None, None
            await self.broadcast_state()

    async def broadcast_chat(self, msg):
        await self.channel_layer.group_send(self.room_group_name, {'type': 'send_msg', 'message': {'type': 'chat_message', 'message': msg}})

    async def broadcast_state(self):
        room = ROOMS_UNDERCOVER.get(self.room_code)
        if not room:
            return
        players_list = [{'id': ch, 'name': p['name'], 'is_host': p['is_host'], 'has_voted': ch in room['votes']} for ch, p in room['players'].items()]
        await self.channel_layer.group_send(self.room_group_name, {'type': 'send_msg', 'message': {'type': 'room_state', 'state': room['state'], 'players': players_list, 'clue': room['clue'], 'messages': room['messages'], 'difficulty': room['difficulty'], 'media_type': room['media_type']}})
        if room['state'] in ['playing', 'revealed']:
            for ch, p in room['players'].items():
                await self.channel_layer.send(ch, {'type': 'send_msg', 'message': {'type': 'private_role', 'role': p['role'], 'word': p['word'], 'image': p['image']}})

    async def start_game_logic(self, room):
        data = await sync_to_async(animetix_service.load_data)(room['media_type'])
        if not data: return
        
        # Application de la difficulté
        media_settings = DIFFICULTY_SETTINGS.get(room['media_type'], DIFFICULTY_SETTINGS["Anime"])
        rank_limit = media_settings.get(room['difficulty'], 300)
        
        # Robustesse : certains objets ont 'name' au lieu de 'title' (ex: Characters)
        valid = [t for t in data['lookup'] if (t.get('title') or t.get('name')) in data['title_to_full_data']]
        if rank_limit is not None:
            valid = valid[:rank_limit]
            
        if not valid: return
        
        civil = random.choice(valid)
        civil_label = civil.get('title') or civil.get('name')
        civil_id = data['title_to_full_data'][civil_label]['id']
        undercover_title = None
        try:
            coll_name = "character_vibe" if room['media_type'] == 'Character' else f"{room['media_type'].lower()}_thematic"
            coll = await sync_to_async(animetix_service.get_chroma_collection)(coll_name)
            res = await sync_to_async(coll.query)(query_embeddings=(await sync_to_async(coll.get)(ids=[str(civil_id)], include=['embeddings']))['embeddings'], n_results=5)
            # Robustesse ici aussi
            undercover_title = random.choice([ (m.get('title') or m.get('name')) for m in res['metadatas'][0] if str(m['id']) != str(civil_id)])
        except: undercover_title = random.choice([ (t.get('title') or t.get('name')) for t in valid if (t.get('title') or t.get('name')) != civil_label])
        
        lang_service = LangChainService()
        clue = await sync_to_async(lang_service.generate_undercover_clue)(room['media_type'], civil_label, undercover_title, "Français")
        
        u_id = random.choice(list(room['players'].keys()))
        for ch, p in room['players'].items():
            obj = data['title_to_full_data'][undercover_title if ch == u_id else civil_label]
            p['role'], p['word'], p['image'] = ('Undercover' if ch == u_id else 'Civil'), (obj.get('title') or obj.get('name')), obj.get('image')
        room['clue'], room['state'] = clue, 'playing'
        await self.broadcast_state()

    async def send_msg(self, event): await self.send(text_data=json.dumps(event['message']))

# --- 2. CONSUMER CODEMANGA ---
class CodeMangaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code'].upper()
        self.room_group_name = f'codemanga_{self.room_code}'
        if self.room_code not in ROOMS_CODEMANGA:
            ROOMS_CODEMANGA[self.room_code] = {'host': self.channel_name, 'players': {}, 'state': 'lobby', 'grid': [], 'turn': 'blue', 'blue_score': 0, 'red_score': 0, 'winner': None}
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        ROOMS_CODEMANGA[self.room_code]['players'][self.channel_name] = {'name': f'Fan #{random.randint(100, 999)}', 'team': None, 'role': None}
        await self.accept()
        await self.broadcast_state()

    async def disconnect(self, close_code): await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        room = ROOMS_CODEMANGA.get(self.room_code)
        if not room: return
        if action == 'set_player': room['players'][self.channel_name].update({'name': data.get('name', 'Anonyme'), 'team': data.get('team', 'blue'), 'role': data.get('role', 'operative')})
        elif action == 'start_game': 
            await self.generate_grid(room)
            room['state'] = 'playing'
            # On notifie tout le monde de changer de page
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_msg',
                'message': {
                    'type': 'redirect',
                    'url': f'/codemanga/game/{self.room_code}/' # URL en dur ou via reverse (plus simple en dur ici pour le consumer)
                }
            })
        elif action == 'click_card': await self.handle_card_click(room, data.get('index'))
        await self.broadcast_state()

    async def generate_grid(self, room):
        data = await sync_to_async(animetix_service.load_data)('Anime')
        if not data: return
        # RETOUR AU MODE 25 CARTES (5x5)
        selected = random.sample(list(data['db']), 25)
        roles = (['blue'] * 9) + (['red'] * 8) + (['neutral'] * 7) + (['assassin'] * 1); random.shuffle(roles)
        room['grid'] = [{
            'title': selected[i].get('title'),
            'title_en': selected[i].get('title_english') or selected[i].get('title'),
            'title_jp': selected[i].get('title_native') or selected[i].get('title'),
            'image': selected[i].get('image'),
            'role': roles[i],
            'revealed': False
        } for i in range(25)]
        room['blue_score'] = 0; room['red_score'] = 0; room['turn'] = 'blue'; room['winner'] = None

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
        room = ROOMS_CODEMANGA.get(self.room_code)
        if not room: return
        
        public_grid = [{
            'title': c['title'],
            'title_en': c['title_en'],
            'title_jp': c['title_jp'],
            'image': c['image'],
            'revealed': c['revealed'],
            'role': (c['role'] if c['revealed'] else 'unknown')
        } for c in room['grid']]
        
        for ch, p in room['players'].items():
            # Les spymasters voient tout, les operatives voient public_grid
            grid_to_send = room['grid'] if p['role'] == 'spymaster' else public_grid
            
            await self.channel_layer.send(ch, {
                'type': 'send_msg',
                'message': {
                    'type': 'state',
                    'room': {
                        'state': room['state'],
                        'grid': grid_to_send,
                        'turn': room['turn'],
                        'blue_score': room['blue_score'],
                        'red_score': room['red_score'],
                        'winner': room['winner'],
                        'players': list(room['players'].values())
                    },
                    'my_role': p['role'],
                    'my_team': p['team']
                }
            })

    async def send_msg(self, event): await self.send(text_data=json.dumps(event['message']))

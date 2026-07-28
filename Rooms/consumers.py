import json
import asyncio
import time
import secrets
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken
from .models import Room, RoomMember
from QuestionsDirectory.models import Question, QuestionOption


class RoomConsumer(AsyncWebsocketConsumer):
    active_games = {}
    room_locks = {}
    global_lock = asyncio.Lock()
    host_disconnect_timers = {}

    async def connect(self):
        self.room_code = None
        await self.accept()

        query = self.scope['query_string'].decode()
        token = None
        for param in query.split('&'):
            if param.startswith('token='):
                token = param[6:]
                break

        self.user = await self.authenticate_user(token)
        if not self.user:
            await self.close(code=4001)

    async def disconnect(self, close_code):
        if self.room_code:
            code = self.room_code
            is_host = await self.is_user_host(self.user, code)
            await self.channel_layer.group_discard(f'room_{code}', self.channel_name)
            members = await self.get_room_members(code)
            await self.channel_layer.group_send(
                f'room_{code}',
                {
                    'type': 'room_broadcast',
                    'message': {
                        'type': 'player_disconnected',
                        'user': {'id': self.user.id, 'username': self.user.username},
                        'members': members,
                    },
                }
            )
            if is_host:
                await self.start_host_disconnect_timer(code)
            self.room_code = None

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                await self.send_error('Invalid JSON')
                return

            msg_type = data.get('type')
            handler = {
                'create_room': self.handle_create_room,
                'join_room': self.handle_join_room,
                'start_game': self.handle_start_game,
                'submit_answer': self.handle_submit_answer,
                'leave_room': self.handle_leave_room,
            }.get(msg_type)

            if handler:
                await handler(data)
            else:
                await self.send_error(f'Unknown message type: {msg_type}')

    async def authenticate_user(self, token):
        if not token:
            return None
        try:
            access_token = AccessToken(token)
            user = await database_sync_to_async(User.objects.get)(
                id=access_token['user_id']
            )
            return user
        except Exception:
            return None

    async def send_error(self, message):
        await self.send(text_data=json.dumps({'type': 'error', 'message': message}))

    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))

    async def get_room_lock(self, room_code):
        async with self.global_lock:
            if room_code not in self.room_locks:
                self.room_locks[room_code] = asyncio.Lock()
            return self.room_locks[room_code]

    # ---- Room Management ----

    async def handle_create_room(self, data):
        if self.room_code:
            await self.send_error('You are already in a room')
            return

        question_deck_id = data.get('question_deck_id')
        time_limit = data.get('time_limit', 10)

        if not question_deck_id:
            await self.send_error('question_deck_id is required')
            return

        try:
            time_limit = int(time_limit)
            if time_limit < 5 or time_limit > 60:
                await self.send_error('time_limit must be between 5 and 60 seconds')
                return
        except (ValueError, TypeError):
            await self.send_error('Invalid time_limit')
            return

        room = await self.create_room_in_db(
            self.user, question_deck_id, time_limit
        )
        if not room:
            await self.send_error('Failed to create room')
            return

        self.room_code = room['code']
        await self.channel_layer.group_add(
            f'room_{self.room_code}', self.channel_name
        )

        await self.send_message({
            'type': 'room_created',
            'code': self.room_code,
            'room': room,
        })

    async def handle_join_room(self, data):
        if self.room_code:
            await self.send_error('You are already in a room. Leave first.')
            return

        code = data.get('code', '').strip().upper()

        room_data = await self.join_room_in_db(self.user, code)
        if not room_data:
            await self.send_error('Invalid or unavailable room code')
            return

        if room_data.get('is_host'):
            await self.cancel_host_disconnect_timer(code)

        self.room_code = code
        await self.channel_layer.group_add(
            f'room_{self.room_code}', self.channel_name
        )

        await self.send_message({
            'type': 'room_joined',
            'code': code,
            'members': room_data['members'],
            'is_host': room_data.get('is_host', False),
        })

        if room_data.get('is_new'):
            await self.channel_layer.group_send(
                f'room_{self.room_code}',
                {
                    'type': 'room_broadcast',
                    'message': {
                        'type': 'player_joined',
                        'user': {'id': self.user.id, 'username': self.user.username},
                        'members': room_data['members'],
                    },
                }
            )

        game = self.active_games.get(code)
        if game and game['current_index'] < len(game['questions']):
            scores_list = []
            for m in room_data['members']:
                scores_list.append({
                    'user': {'id': m['user_id'], 'username': m['username']},
                    'score': game['scores'].get(m['user_id'], 0),
                })
            q_data = game['questions'][game['current_index']]
            await self.send_message({
                'type': 'game_state',
                'current_index': game['current_index'],
                'total_questions': game['total_questions'],
                'scores': scores_list,
            })
            await self.send_message({
                'type': 'question',
                'question_index': game['current_index'] + 1,
                'total': game['total_questions'],
                'question': q_data,
                'time_limit': game['time_limit'],
            })

    async def handle_leave_room(self, data=None):
        if not self.room_code:
            await self.send_error('You are not in a room')
            return
        await self.leave_room_internal()

    async def leave_room_internal(self):
        code = self.room_code
        self.room_code = None

        await self.channel_layer.group_discard(
            f'room_{code}', self.channel_name
        )

        room_data = await self.remove_member_from_room(self.user, code)
        if room_data:
            await self.channel_layer.group_send(
                f'room_{code}',
                {
                    'type': 'room_broadcast',
                    'message': {
                        'type': 'player_left',
                        'user': {'id': self.user.id, 'username': self.user.username},
                        'members': room_data['members'],
                    },
                }
            )

    # ---- Game Logic ----

    async def handle_start_game(self, data):
        if not self.room_code:
            await self.send_error('You are not in a room')
            return

        code = self.room_code
        lock = await self.get_room_lock(code)
        async with lock:
            if code in self.active_games:
                await self.send_error('Game already in progress')
                return

            room_info = await self.get_room_info(code)
            if not room_info:
                await self.send_error('Room not found')
                return

            if room_info['host_id'] != self.user.id:
                await self.send_error('Only the host can start the game')
                return

            if room_info['status'] != 'LOBBY':
                await self.send_error('Game has already started or ended')
                return

            questions = await self.load_questions(room_info['deck_id'])
            if not questions:
                await self.send_error('No questions available for this deck')
                return

            await self.set_room_status(code, 'IN_PROGRESS')

            self.active_games[code] = {
                'questions': questions,
                'current_index': 0,
                'scores': {},
                'player_answers': {},
                'question_start_time': None,
                'timer_task': None,
                'time_limit': room_info['time_limit'],
                'host_id': room_info['host_id'],
                'total_questions': len(questions),
                'players_answered': set(),
            }

            members = await self.get_room_members(code)
            for m in members:
                self.active_games[code]['scores'][m['user_id']] = m['score']

        await self.channel_layer.group_send(
            f'room_{code}',
            {
                'type': 'room_broadcast',
                'message': {
                    'type': 'game_started',
                    'total_questions': len(questions),
                    'time_limit': room_info['time_limit'],
                },
            }
        )

        await asyncio.sleep(1)
        await self.send_current_question(code)

    async def send_current_question(self, code):
        game = self.active_games.get(code)
        if not game:
            return

        idx = game['current_index']
        if idx >= len(game['questions']):
            await self.end_game(code)
            return

        question_data = game['questions'][idx]
        game['question_start_time'] = time.time()
        game['player_answers'] = {}
        game['players_answered'] = set()

        await self.channel_layer.group_send(
            f'room_{code}',
            {
                'type': 'room_broadcast',
                'message': {
                    'type': 'question',
                    'question_index': idx + 1,
                    'total': game['total_questions'],
                    'question': question_data,
                    'time_limit': game['time_limit'],
                },
            }
        )

        loop = asyncio.get_running_loop()
        game['timer_task'] = loop.call_later(
            game['time_limit'],
            lambda: asyncio.ensure_future(self.on_question_timeout(code))
        )

    async def on_question_timeout(self, code):
        game = self.active_games.get(code)
        if not game:
            return

        lock = await self.get_room_lock(code)
        async with lock:
            if code not in self.active_games:
                return
            await self.finalize_question(code)

    async def handle_submit_answer(self, data):
        if not self.room_code:
            await self.send_error('You are not in a room')
            return

        code = self.room_code
        game = self.active_games.get(code)
        if not game:
            await self.send_error('No active game')
            return

        uid = self.user.id
        lock = await self.get_room_lock(code)
        async with lock:
            if code not in self.active_games:
                await self.send_error('No active game')
                return

            if uid in game['players_answered']:
                await self.send_error('Already answered this question')
                return

            option_id = data.get('option_id')
            if not option_id:
                await self.send_error('option_id is required')
                return

            current_q = game['questions'][game['current_index']]
            correct = option_id == current_q['correct_option_id']
            elapsed = time.time() - game['question_start_time']

            game['player_answers'][uid] = {
                'option_id': option_id,
                'correct': correct,
            }
            game['players_answered'].add(uid)

            if correct:
                game['scores'][uid] = game['scores'].get(uid, 0) + 10

        await self.send_message({
            'type': 'answer_result',
            'correct': correct,
            'correct_option_id': current_q['correct_option_id'],
            'score': game['scores'].get(uid, 0),
            'time_taken': round(elapsed, 2),
        })

        members = await self.get_room_members(code)
        total = len([m for m in members if not m.get('is_host')])
        if len(game['players_answered']) >= total:
            lock2 = await self.get_room_lock(code)
            async with lock2:
                if code in self.active_games:
                    if game['timer_task']:
                        game['timer_task'].cancel()
                    await self.finalize_question(code)

    async def finalize_question(self, code):
        game = self.active_games.get(code)
        if not game:
            return

        scores_list = []
        members = await self.get_room_members(code)
        for m in members:
            uid = m['user_id']
            scores_list.append({
                'user': {'id': uid, 'username': m['username']},
                'score': game['scores'].get(uid, 0),
            })

        await self.channel_layer.group_send(
            f'room_{code}',
            {
                'type': 'room_broadcast',
                'message': {
                    'type': 'score_update',
                    'scores': scores_list,
                },
            }
        )

        game['current_index'] += 1
        await asyncio.sleep(1)
        await self.send_current_question(code)

    async def end_game(self, code):
        game = self.active_games.get(code)
        if not game:
            return

        await self.set_room_status(code, 'FINISHED')

        await self.persist_scores(code, game['scores'])

        sorted_players = sorted(
            game['scores'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        results = []
        for rank, (uid, score) in enumerate(sorted_players, 1):
            username = await self.get_username(uid)
            results.append({
                'user': {'id': uid, 'username': username},
                'score': score,
                'rank': rank,
            })

        await self.channel_layer.group_send(
            f'room_{code}',
            {
                'type': 'room_broadcast',
                'message': {
                    'type': 'game_ended',
                    'results': results,
                },
            }
        )

        self.active_games.pop(code, None)
        self.room_locks.pop(code, None)

    # ---- Host Disconnect Timer ----

    async def start_host_disconnect_timer(self, room_code):
        loop = asyncio.get_running_loop()
        task = loop.create_task(self._host_disconnect_timeout(room_code))
        self.__class__.host_disconnect_timers[room_code] = task

    async def _host_disconnect_timeout(self, room_code):
        try:
            await asyncio.sleep(120)
            if room_code not in self.__class__.host_disconnect_timers:
                return
            await self.channel_layer.group_send(
                f'room_{room_code}',
                {
                    'type': 'room_broadcast',
                    'message': {
                        'type': 'room_deleted',
                        'reason': 'Host disconnected',
                    },
                }
            )
            self.__class__.active_games.pop(room_code, None)
            self.__class__.room_locks.pop(room_code, None)
            await self.delete_room(room_code)
        except asyncio.CancelledError:
            pass
        finally:
            self.__class__.host_disconnect_timers.pop(room_code, None)

    async def cancel_host_disconnect_timer(self, room_code):
        task = self.__class__.host_disconnect_timers.pop(room_code, None)
        if task:
            task.cancel()

    # ---- DB Helpers ----

    @database_sync_to_async
    def create_room_in_db(self, user, deck_id, time_limit):
        from QuestionsDirectory.models import QuestionDeck
        try:
            deck = QuestionDeck.objects.get(id=deck_id)
        except QuestionDeck.DoesNotExist:
            return None

        code = self._generate_room_code()
        if not code:
            return None

        room = Room.objects.create(
            code=code,
            host=user,
            question_deck=deck,
            time_limit=time_limit,
            status='LOBBY',
        )
        RoomMember.objects.create(room=room, user=user, score=0)

        members = [
            {
                'user_id': user.id,
                'username': user.username,
                'score': 0,
                'is_host': True,
            }
        ]
        return {
            'code': code,
            'id': room.id,
            'host_id': user.id,
            'time_limit': time_limit,
            'question_deck_id': deck_id,
            'status': 'LOBBY',
            'members': members,
        }

    @database_sync_to_async
    def join_room_in_db(self, user, code):
        try:
            room = Room.objects.get(code=code)
            if room.status not in ('LOBBY', 'IN_PROGRESS'):
                return None
        except Room.DoesNotExist:
            return None

        is_new = not RoomMember.objects.filter(room=room, user=user).exists()
        if is_new:
            RoomMember.objects.create(room=room, user=user, score=0)

        members = []
        for m in room.members.select_related('user').all():
            members.append({
                'user_id': m.user.id,
                'username': m.user.username,
                'score': m.score,
                'is_host': m.user == room.host,
            })

        return {
            'members': members,
            'is_new': is_new,
            'is_host': user == room.host,
        }

    @database_sync_to_async
    def remove_member_from_room(self, user, code):
        try:
            room = Room.objects.get(code=code)
        except Room.DoesNotExist:
            return None

        RoomMember.objects.filter(room=room, user=user).delete()

        remaining = list(room.members.select_related('user').all())
        members = []
        for m in remaining:
            members.append({
                'user_id': m.user.id,
                'username': m.user.username,
                'score': m.score,
                'is_host': m.user == room.host,
            })

        return {
            'members': members,
            'is_empty': len(remaining) == 0,
        }

    @database_sync_to_async
    def get_room_info(self, code):
        try:
            room = Room.objects.get(code=code)
            return {
                'host_id': room.host.id,
                'status': room.status,
                'deck_id': room.question_deck_id,
                'time_limit': room.time_limit,
            }
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def get_room_members(self, code):
        try:
            room = Room.objects.get(code=code)
            members = []
            for m in room.members.select_related('user').all():
                members.append({
                    'user_id': m.user.id,
                    'username': m.user.username,
                    'score': m.score,
                    'is_host': m.user == room.host,
                })
            return members
        except Room.DoesNotExist:
            return []

    @database_sync_to_async
    def set_room_status(self, code, status):
        Room.objects.filter(code=code).update(status=status)

    @database_sync_to_async
    def persist_scores(self, code, scores):
        members = RoomMember.objects.filter(room__code=code)
        for m in members:
            if m.user.id in scores:
                m.score = scores[m.user.id]
                m.save()

    @database_sync_to_async
    def get_username(self, user_id):
        try:
            return User.objects.get(id=user_id).username
        except User.DoesNotExist:
            return 'Unknown'

    @database_sync_to_async
    def cleanup_empty_room(self, code):
        Room.objects.filter(code=code).delete()

    @database_sync_to_async
    def is_user_host(self, user, room_code):
        try:
            room = Room.objects.get(code=room_code)
            return room.host == user
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def delete_room(self, code):
        Room.objects.filter(code=code).delete()

    @database_sync_to_async
    def load_questions(self, deck_id):
        questions = Question.objects.filter(deck_id=deck_id).prefetch_related('options')
        pool = []
        for q in questions:
            options = []
            correct_id = None
            for opt in q.options.all():
                options.append({
                    'id': opt.id,
                    'text': opt.option_text,
                })
                if opt.is_correct:
                    correct_id = opt.id

            pool.append({
                'id': q.id,
                'definition': q.definition,
                'usage_example': q.usage_example,
                'difficulty': q.difficulty,
                'options': options,
                'correct_option_id': correct_id,
            })

        random.shuffle(pool)
        return pool[:20]

    def _generate_room_code(self):
        letters = secrets.token_urlsafe(3).upper()[:3]
        nums = ''.join(str(random.randint(0, 9)) for _ in range(3))
        code = f'QUIZ-{letters}{nums}'
        if not Room.objects.filter(code=code).exists():
            return code
        return None

    # ---- Group Broadcast Handler ----

    async def room_broadcast(self, event):
        await self.send(text_data=json.dumps(event['message']))

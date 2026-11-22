from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import EscapeRoom, Room, Stage, Puzzle, UserEscapeSession, EscapeSettlement, Hint, HintUsage
from .services import start_session, register_attempt, use_hint, expire_session_if_needed

class EscapeFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='player', password='password123')
        self.other = get_user_model().objects.create_user(username='other', password='password123')
        self.adventure = EscapeRoom.objects.create(name='Test', slug='test', description='Test',
            estimated_duration=10, time_limit_seconds=600, final_solution_hash='')
        self.puzzles = []
        for i in range(2):
            room = Room.objects.create(escape_room=self.adventure, name=f'Sala {i}',
                description='Test', order=i+1, door_solution_hash='', final_fragment='')
            for j in range(3):
                stage = Stage.objects.create(room=room, name=f'Fase {i}-{j}', description='Test', order=j+1)
                self.puzzles.append(Puzzle.objects.create(stage=stage, title='Pregunta', description='Test',
                    type='TEXT', solution_hash='sí', points=10, max_attempts=3))

    def test_six_phases_in_order_and_idempotent_settlement(self):
        s = start_session(user=self.user, escape_room=self.adventure)
        for idx, puzzle in enumerate(self.puzzles):
            self.assertEqual(s.current_stage_id, puzzle.stage_id)
            result = register_attempt(session=s, puzzle=puzzle, answer='sí')
            s.refresh_from_db()
            self.assertTrue(result['is_correct'])
            self.assertEqual(s.status, 'COMPLETED' if idx == 5 else 'PLAYING')
        self.assertEqual(EscapeSettlement.objects.filter(session=s).count(), 1)
        self.assertEqual(EscapeSettlement.objects.filter(session=s).count(), 1)

    def test_wrong_answer_limit(self):
        s = start_session(user=self.user, escape_room=self.adventure)
        for _ in range(3):
            register_attempt(session=s, puzzle=self.puzzles[0], answer='no')
        s.refresh_from_db()
        self.assertEqual(s.status, 'FAILED')

    def test_expired_session(self):
        s = start_session(user=self.user, escape_room=self.adventure)
        UserEscapeSession.objects.filter(pk=s.pk).update(active_since=timezone.now()-timedelta(seconds=601))
        s.refresh_from_db()
        self.assertTrue(expire_session_if_needed(s))
        self.assertEqual(s.status, 'FAILED')

    def test_other_user_cannot_read_session(self):
        s = start_session(user=self.user, escape_room=self.adventure)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('escape_arenas:play', kwargs={'pk':s.pk})).status_code, 404)

    def test_anonymous_redirected(self):
        self.assertEqual(self.client.get(reverse('escape_arenas:room_list')).status_code, 302)

    def test_hint_only_once(self):
        s = start_session(user=self.user, escape_room=self.adventure)
        hint = Hint.objects.create(puzzle=self.puzzles[0], text='Pista', order=1, penalty_points=5)
        self.assertTrue(use_hint(s,hint))
        self.assertFalse(use_hint(s,hint))
        self.assertEqual(HintUsage.objects.filter(session=s).count(),1)

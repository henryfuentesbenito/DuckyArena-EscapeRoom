"""Regression tests for the approved prehistory game rules and state isolation."""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from .models import EscapeRoom, Puzzle, Hint
from .services import PREHISTORY_RULES, check_stage_answer, start_session, pause_session
from .world import interact, WorldActionError


class PrehistoryContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_escape_prehistory', verbosity=0)
        cls.adventure = EscapeRoom.objects.get(slug='laboratorio-tiempo-prehistoria-v1')
        cls.user = get_user_model().objects.create_user(username='escape_pre_hito4', password='testpass')

    def test_eight_challenges_and_three_rooms(self):
        self.assertEqual(self.adventure.rooms.count(), 3)
        self.assertEqual(Puzzle.objects.filter(stage__room__escape_room=self.adventure).count(), 8)
        self.assertEqual(Hint.objects.filter(puzzle__stage__room__escape_room=self.adventure).count(), 24)
        self.assertEqual(self.adventure.time_limit_seconds, 1500)
        self.assertEqual(PREHISTORY_RULES['time_bonus_max'], 200)

    def test_sequence_validation_is_server_side(self):
        puzzle = Puzzle.objects.get(stage__name='Energía perdida', stage__room__escape_room=self.adventure)
        self.assertTrue(check_stage_answer(puzzle=puzzle, submitted_answer='recoger,colocar,activar,verificar'))
        self.assertFalse(check_stage_answer(puzzle=puzzle, submitted_answer='verificar,activar,colocar,recoger'))
        self.assertNotIn('solution_hash', puzzle.config)

    def test_paused_session_cannot_change_world(self):
        session = start_session(user=self.user, escape_room=self.adventure)
        pause_session(session)
        with self.assertRaises(WorldActionError):
            interact(session=session, target_key='cave-crystal', action='collect')

    def test_collection_is_idempotent(self):
        session = start_session(user=self.user, escape_room=self.adventure)
        interact(session=session, target_key='cave-crystal', action='collect')
        interact(session=session, target_key='cave-crystal', action='collect')
        self.assertEqual(session.world_items.get(item__key='energy-crystal').quantity, 1)

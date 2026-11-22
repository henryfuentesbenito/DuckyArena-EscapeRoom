from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from .models import EscapeRoom, Room, UserEscapeSession, EscapeSettlement
from .services import pause_session, resume_session, get_remaining_seconds, expire_session_if_needed
from .ducky_adapter import public_ducky

class Hito4Regressions(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="escape_regression", password="test")
        adventure = EscapeRoom.objects.create(name="Regression", slug="regression", description="Test", estimated_duration=25, time_limit_seconds=1500, final_solution_hash="x")
        room = Room.objects.create(escape_room=adventure, name="Cueva", description="Test", order=1, door_solution_hash="x", final_fragment="x")
        now = timezone.now()
        self.session = UserEscapeSession.objects.create(user=self.user, escape_room=adventure, current_room=room, status="PLAYING", started_at=now, active_since=now, expires_at=now + timedelta(seconds=1500), rules_snapshot={"time_limit_seconds":1500})

    def test_pause_stops_clock_and_blocks_expiry(self):
        paused = pause_session(self.session)
        self.assertEqual(paused.status, "PAUSED")
        remaining = get_remaining_seconds(paused)
        self.assertFalse(expire_session_if_needed(paused))
        self.assertEqual(get_remaining_seconds(paused), remaining)
        self.assertEqual(pause_session(paused).pause_count, 1)

    def test_resume_is_idempotent(self):
        paused = pause_session(self.session)
        resumed = resume_session(paused)
        self.assertEqual(resumed.status, "PLAYING")
        self.assertEqual(resume_session(resumed).pause_count, 1)

    def test_ducky_adapter_has_safe_empty_state(self):
        self.assertFalse(public_ducky(self.user)["exists"])

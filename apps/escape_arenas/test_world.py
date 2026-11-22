from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import EscapeRoom, Room, UserEscapeSession, EscapeItemDefinition, EscapeInteractable
from .world import interact, public_world, WorldActionError


class EscapeWorldTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="worldtester", password="test")
        adventure = EscapeRoom.objects.create(name="Test", slug="test-world", description="Test", estimated_duration=20, final_solution_hash="test")
        room = Room.objects.create(escape_room=adventure, name="Cueva", description="", order=1, door_solution_hash="x", final_fragment="x")
        self.session = UserEscapeSession.objects.create(user=user, escape_room=adventure, current_room=room, status="PLAYING", started_at=timezone.now(), expires_at=timezone.now()+timedelta(minutes=20))
        EscapeItemDefinition.objects.create(escape_room=adventure, key="crystal", name="Cristal")
        EscapeInteractable.objects.create(room=room, key="crystal-rock", label="Cristal", actions={"collect": {"item": "crystal"}})
        EscapeInteractable.objects.create(room=room, key="altar", label="Altar", actions={"use": {"requires_item": "crystal", "consume": True, "next_state": "lit"}})

    def test_collect_is_idempotent(self):
        for _ in range(2):
            interact(session=self.session, target_key="crystal-rock", action="collect")
        self.assertEqual(public_world(self.session)["inventory"][0]["quantity"], 1)

    def test_use_consumes_once(self):
        interact(session=self.session, target_key="crystal-rock", action="collect")
        for _ in range(2):
            interact(session=self.session, target_key="altar", action="use", item_key="crystal")
        self.assertEqual(public_world(self.session)["inventory"], [])

    def test_use_requires_ownership(self):
        with self.assertRaises(WorldActionError):
            interact(session=self.session, target_key="altar", action="use", item_key="crystal")

    def test_world_prerequisite_requires_lit_altar(self):
        from .models import Stage, Puzzle
        from .services import check_stage_answer, register_attempt
        stage = Stage.objects.create(room=self.session.current_room, name="Energy", order=1)
        puzzle = Puzzle.objects.create(stage=stage, title="Energy", description="Order",
            type="SEQUENCE", solution_hash="a,b", config={"required_world": {"altar": "lit"}})
        self.session.current_stage = stage
        self.session.save(update_fields=["current_stage"])
        with self.assertRaisesMessage(ValueError, "mecanismos"):
            register_attempt(session=self.session, puzzle=puzzle, answer="a,b")
        interact(session=self.session, target_key="crystal-rock", action="collect")
        interact(session=self.session, target_key="altar", action="use", item_key="crystal")
        self.assertTrue(check_stage_answer(puzzle=puzzle, submitted_answer="a,b"))

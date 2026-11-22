from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.management import call_command
from .models import EscapeRoom
from .services import start_session


class CleanCatalogTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="catalogplayer", password="test-password-123")
        self.client.force_login(self.user)
        call_command("seed_escape_prehistory", verbosity=0)

    def test_only_official_adventure_in_catalog(self):
        EscapeRoom.objects.create(name="Demo vieja", slug="escape-demo-seis-fases", is_active=True, description="Demo archivada", estimated_duration=15, final_solution_hash="demo")
        response = self.client.get(reverse("escape_arenas:room_list"))
        self.assertContains(response, "laboratorio")
        self.assertNotContains(response, "Demo vieja")
        self.assertEqual(self.client.get(reverse("escape_arenas:room_detail", args=["escape-demo-seis-fases"])).status_code, 404)

    def test_old_play_link_redirects_to_phaser(self):
        room = EscapeRoom.objects.get(slug="laboratorio-tiempo-prehistoria-v1")
        session = start_session(user=self.user, escape_room=room)
        response = self.client.get(reverse("escape_arenas:play", args=[session.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"/escape/game/?session={session.pk}")

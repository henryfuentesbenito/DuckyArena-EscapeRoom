from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.management import call_command
from apps.escape_arenas.models import EscapeRoom


class UnifiedMissionCenterTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="mission_center_player", password="test-secret-123")
        self.client.force_login(self.user)
        call_command("seed_escape_prehistory", verbosity=0)

    def test_catalog_includes_rules_and_start_form(self):
        response = self.client.get(reverse("escape_arenas:room_list"), {"theme": "LAB"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Centro de misiones")
        self.assertContains(response, "Reglas de la misión")
        self.assertContains(response, "Iniciar aventura")
        self.assertContains(response, reverse("escape_arenas:escape_start", args=["laboratorio-tiempo-prehistoria-v1"]))

    def test_old_detail_redirects_to_unified_catalog(self):
        response = self.client.get(reverse("escape_arenas:room_detail", args=["laboratorio-tiempo-prehistoria-v1"]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("theme=LAB", response.url)
        self.assertIn("mission=laboratorio-tiempo-prehistoria-v1", response.url)

    def test_catalog_preserves_theme_filter(self):
        response = self.client.get(reverse("escape_arenas:room_list"), {"theme": "PRISON"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No hay aventuras disponibles")

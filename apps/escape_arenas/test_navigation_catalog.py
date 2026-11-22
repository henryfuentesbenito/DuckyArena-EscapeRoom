from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import EscapeRoom
from .management.commands.seed_escape_prehistory import Command

class EscapeNavigationCatalogTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="nav-escape", password="strong-pass-123")
        self.client.force_login(self.user)
        Command().handle()

    def test_catalog_filter_keeps_lab_adventure(self):
        response = self.client.get(reverse("escape_arenas:room_list"), {"theme":"LAB"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El laboratorio del tiempo")
        self.assertContains(response, "Volver a temáticas")

    def test_hub_returns_ducky_payload(self):
        response = self.client.get(reverse("escape_arenas:hub_data"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("ducky", response.json())

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

class EscapeTeam5IntegrationTests(TestCase):
    def test_escape_catalog_requires_login(self):
        response = self.client.get(reverse('escape_arenas:room_list'))
        self.assertEqual(response.status_code, 302)

    def test_escape_catalog_works_for_team5_user(self):
        user = get_user_model().objects.create_user(username='escape_test_user', password='demo-pass-123')
        self.client.force_login(user)
        response = self.client.get(reverse('escape_arenas:room_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DuckyArena')

    def test_escape_hub_requires_login(self):
        response = self.client.get(reverse('escape_arenas:hub_data'))
        self.assertEqual(response.status_code, 302)

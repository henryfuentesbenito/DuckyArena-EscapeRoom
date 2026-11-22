from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.ecomotor.models import Specialization, UserSpecializationProgress, SpecializationXPEvent
from apps.ecomotor.specialization_xp_service import grant_specialization_xp
from apps.users.models import UserProfileEcomotor


class TrainingSpecializationXPTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='training_spec_user', password='testing-only-password')
        self.profile = UserProfileEcomotor.objects.create(
            user=self.user, current_level=1, current_stage_code='demo-stage',
            active_specialization_code='gamer')
        self.gamer = Specialization.objects.create(code='gamer', name='Gamer')
        self.other = Specialization.objects.create(code='developer', name='Developer')
        self.first = UserSpecializationProgress.objects.create(profile=self.profile, specialization=self.gamer)
        self.second = UserSpecializationProgress.objects.create(profile=self.profile, specialization=self.other)

    def test_grant_and_replay_do_not_duplicate(self):
        first = grant_specialization_xp(self.profile, 5, 'training:xp:attempt:101')
        replay = grant_specialization_xp(self.profile, 5, 'training:xp:attempt:101')
        self.first.refresh_from_db()
        self.assertEqual(self.first.domain_xp_total, 5)
        self.assertEqual(first.pk, replay.pk)
        self.assertEqual(SpecializationXPEvent.objects.count(), 1)

    def test_replay_after_switch_does_not_credit_other_branch(self):
        grant_specialization_xp(self.profile, 5, 'training:xp:attempt:102')
        self.profile.active_specialization_code = 'developer'
        self.profile.save(update_fields=['active_specialization_code'])
        grant_specialization_xp(self.profile, 5, 'training:xp:attempt:102')
        self.second.refresh_from_db()
        self.assertEqual(self.second.domain_xp_total, 0)
        grant_specialization_xp(self.profile, 5, 'training:xp:attempt:103')
        self.second.refresh_from_db()
        self.assertEqual(self.second.domain_xp_total, 5)

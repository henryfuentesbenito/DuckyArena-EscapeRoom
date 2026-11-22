"""Idempotent local Training XP for the currently active specialization.

This does not invent level thresholds or official Core XP rules: only the
already-existing per-specialization XP total is advanced.
"""
from django.db import transaction
from django.db.models import F
from apps.users.models import UserProfileEcomotor
from .models import SpecializationXPEvent, UserSpecializationProgress


def grant_specialization_xp(profile, amount, operation_key):
    if not isinstance(profile, UserProfileEcomotor) or profile.pk is None:
        raise ValueError('Persisted Ecomotor profile required')
    if type(amount) is not int or amount <= 0:
        raise ValueError('Positive integer XP required')
    if not isinstance(operation_key, str) or not 1 <= len(operation_key) <= 255:
        raise ValueError('Invalid XP operation key')
    with transaction.atomic():
        current = UserProfileEcomotor.objects.select_for_update().get(pk=profile.pk)
        existing = SpecializationXPEvent.objects.filter(profile=current, operation_key=operation_key).first()
        if existing is not None:
            if existing.amount != amount:
                raise ValueError('XP operation key reused with different amount')
            return existing
        code = current.active_specialization_code
        if not code:
            raise ValueError('Active specialization required')
        progress = UserSpecializationProgress.objects.select_for_update().select_related('specialization').get(
            profile=current, specialization__code=code)
        before = progress.domain_xp_total
        if type(before) is not int or before < 0:
            raise ValueError('Invalid specialization progress')
        after = before + amount
        # SQLite/PostgreSQL BigInteger bounds; prevent accidental overflow.
        if after > 9223372036854775807:
            raise OverflowError('Specialization XP exceeds database bounds')
        event = SpecializationXPEvent.objects.create(
            profile=current, progress=progress, operation_key=operation_key,
            amount=amount, xp_before=before, xp_after=after)
        UserSpecializationProgress.objects.filter(pk=progress.pk).update(domain_xp_total=F('domain_xp_total') + amount)
        return event

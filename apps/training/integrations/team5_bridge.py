"""Integration boundary. Team 5 owns XP, coins, and Duckies.

The bridge is intentionally fail-closed until Team 5 installs a trusted handler.
No browser-provided amount or user identifier is accepted.
"""
from django.conf import settings
from django.db import transaction
from django.utils.module_loading import import_string
from ..models import TrainingAttempt, TrainingRewardDelivery, XP_REWARDS


def ensure_delivery(attempt, first_completion=False):
    xp = XP_REWARDS[attempt.cycle.effective_access_level] if attempt.is_correct else 0
    coin = 1 if attempt.is_correct and first_completion else 0
    delivery, _ = TrainingRewardDelivery.objects.get_or_create(
        attempt=attempt, defaults={'xp_amount': xp, 'coin_amount': coin,
                                  'status': 'PENDING' if xp or coin else 'NO_REWARD'})
    return delivery


def settle_delivery(delivery_id):
    """Invoke only inside the host DB transaction; handler must use the same DB.

    Expected handler: handler(*, user, attempt, xp_amount, coin_amount,
    xp_operation_key, coin_operation_key). It must atomically apply both
    rewards through Team 5's idempotent domain services or raise.
    """
    handler_path = getattr(settings, 'TRAINING_TEAM5_REWARD_HANDLER', None)
    with transaction.atomic():
        delivery = TrainingRewardDelivery.objects.select_for_update().select_related(
            'attempt__user', 'attempt__cycle', 'attempt__exercise').get(pk=delivery_id)
        if delivery.status in ('APPLIED', 'NO_REWARD'):
            return delivery
        if not handler_path:
            return delivery  # Pending is honest; never claim credit.
        handler = import_string(handler_path)
        attempt = delivery.attempt
        try:
            # Handler errors must roll back every wallet/XP mutation.
            with transaction.atomic():
                handler(user=attempt.user, attempt=attempt,
                        xp_amount=delivery.xp_amount, coin_amount=delivery.coin_amount,
                        xp_operation_key=f'training:xp:attempt:{attempt.pk}',
                        coin_operation_key=f'training:coin:cycle:{attempt.cycle_id}:exercise:{attempt.exercise_id}')
                delivery.status = 'APPLIED'
                delivery.last_error = ''
                delivery.save(update_fields=['status', 'last_error', 'updated_at'])
        except Exception as exc:
            delivery.status = 'FAILED'
            delivery.last_error = f'{type(exc).__name__}: {exc}'[:2000]
            delivery.save(update_fields=['status', 'last_error', 'updated_at'])
        return delivery

"""Liquidación local de intentos Training validados por el servidor.

Core no participa. Una sola transacción de la base local coordina XP, Bank y
el registro de entrega. Nunca confiar en importes ni identidades del cliente.
"""
from django.db import transaction
from apps.bank.services import credit_coins, ensure_wallet_provisioned
from apps.integrations.services import grant_xp_and_sync_outfit
from apps.training.models import TrainingRewardDelivery, XP_REWARDS
from apps.users.models import UserProfileEcomotor
from apps.ecomotor.specialization_xp_service import grant_specialization_xp


def training_reward_handler(*, user, attempt, xp_amount, coin_amount,
                            xp_operation_key, coin_operation_key):
    if user.pk != attempt.user_id or not attempt.is_correct:
        raise ValueError('Training attempt identity/correctness mismatch')
    if type(xp_amount) is not int or type(coin_amount) is not int or xp_amount < 0 or coin_amount < 0:
        raise ValueError('Invalid reward amounts')
    if xp_operation_key != f'training:xp:attempt:{attempt.pk}' or coin_operation_key != f'training:coin:cycle:{attempt.cycle_id}:exercise:{attempt.exercise_id}':
        raise ValueError('Invalid operation identity')
    delivery = TrainingRewardDelivery.objects.get(attempt=attempt)
    if delivery.xp_amount != xp_amount or delivery.coin_amount != coin_amount:
        raise ValueError('Reward amounts do not match persisted delivery')
    if xp_amount != XP_REWARDS[attempt.cycle.effective_access_level]:
        raise ValueError('Reward XP does not match the server-side Training policy')
    if coin_amount not in (0, 1) or (coin_amount and not attempt.first_completion):
        raise ValueError('Invalid first-completion coin reward')
    if attempt.cycle.user_id != user.pk or attempt.cycle_id is None or attempt.exercise_id is None:
        raise ValueError('Training attempt/cycle ownership mismatch')
    with transaction.atomic():
        profile = UserProfileEcomotor.objects.select_for_update().get(user=user)
        if xp_amount:
            if profile.active_specialization_code:
                grant_specialization_xp(profile, xp_amount, xp_operation_key)
            else:
                grant_xp_and_sync_outfit(user, xp_amount, xp_operation_key)
        if coin_amount:
            ensure_wallet_provisioned(user)
            credit_coins(user, coin_amount, source='TRAINING', issuing_entity='Training',
                         operation_key=coin_operation_key, reference_type='training_cycle_exercise',
                         reference_id=f'{attempt.cycle_id}:{attempt.exercise_id}',
                         description='First eligible Training completion')

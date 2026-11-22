"""Quiz rewards: 5 XP and 1 DuckyCoin per correct validated answer.
Local integration policy pending approval from Core. Idempotent operation keys per game/player.
"""
from django.db import transaction
from apps.bank.services import credit_coins, ensure_wallet_provisioned
from apps.integrations.services import grant_xp_and_sync_outfit
from apps.ecomotor.specialization_xp_service import grant_specialization_xp
from apps.users.models import UserProfileEcomotor


def settle_quiz_player(game_player):
    from quiz_games.models import Game, GamePlayer, PlayerAnswer
    with transaction.atomic():
        gp = GamePlayer.objects.select_for_update().select_related('game', 'player').get(pk=game_player.pk)
        if gp.game.status != Game.Status.FINISHED or gp.is_settled:
            return False
        # Never trust the mutable leaderboard score for economic awards.
        correct = PlayerAnswer.objects.filter(
            game_player=gp, is_correct=True, question__quiz_id=gp.game.quiz_id
        ).values('question_id').distinct().count()
        xp_amount = correct * 5
        coin_amount = correct
        profile = UserProfileEcomotor.objects.select_for_update().filter(user=gp.player).first()
        if profile is None:
            # Keep unprocessed; no silent loss of a valid reward.
            return False
        if xp_amount:
            if profile.active_specialization_code:
                grant_specialization_xp(profile, xp_amount, f'quiz:xp:game:{gp.game_id}:player:{gp.player_id}')
            else:
                grant_xp_and_sync_outfit(gp.player, xp_amount, f'quiz:xp:game:{gp.game_id}:player:{gp.player_id}')
        if coin_amount:
            ensure_wallet_provisioned(gp.player)
            credit_coins(gp.player, coin_amount, source='QUIZ', issuing_entity='Quiz',
                operation_key=f'quiz:coins:game:{gp.game_id}:player:{gp.player_id}',
                reference_type='quiz_game_player', reference_id=str(gp.pk),
                description='Validated Quiz correct answers')
        gp.is_settled = True
        gp.save(update_fields=['is_settled'])
        return True

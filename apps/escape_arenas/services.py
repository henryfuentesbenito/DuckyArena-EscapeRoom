"""Motor seguro del MVP: una prueba por fase y recompensas locales."""
from datetime import timedelta
from math import ceil
import re
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from .models import (Stage, UserEscapeSession, UserRoomProgress, UserStageProgress,
                     PuzzleAttempt, Hint, HintUsage, EscapeSettlement)

# Reglas versionadas, congeladas en el inicio de cada partida.
PREHISTORY_RULES = {
    'time_limit_seconds': 1500, 'puzzle_points': 100,
    'hint_penalties': [10, 20, 30], 'incorrect_penalty': 5,
    'time_bonus_max': 200, 'master_threshold': 850,
    'rewards_enabled': False, 'scoring_version': 1,
}

def elapsed_seconds(session, now=None):
    now = now or timezone.now()
    consumed = session.active_elapsed_seconds
    if session.status == 'PLAYING':
        since = session.active_since or session.started_at
        if since:
            consumed += max(0, (now - since).total_seconds())
    return consumed

def get_deadline(session):
    if session.status == 'PAUSED':
        return None
    return session.expires_at

def get_remaining_seconds(session):
    limit = session.rules_snapshot.get('time_limit_seconds', session.escape_room.time_limit_seconds)
    return max(0, ceil(limit - elapsed_seconds(session)))

@transaction.atomic
def pause_session(session):
    s = UserEscapeSession.objects.select_for_update().get(pk=session.pk)
    if _expire(s):
        return s
    if s.status == 'PLAYING':
        now = timezone.now()
        s.active_elapsed_seconds = elapsed_seconds(s, now)
        s.active_since = None
        s.status = 'PAUSED'
        s.pause_count += 1
        s.expires_at = None
        s.save(update_fields=['active_elapsed_seconds','active_since','status','pause_count','expires_at','updated_at'])
    return s

@transaction.atomic
def resume_session(session):
    s = UserEscapeSession.objects.select_for_update().get(pk=session.pk)
    if s.status == 'PAUSED':
        now = timezone.now()
        remaining = s.rules_snapshot.get('time_limit_seconds', s.escape_room.time_limit_seconds) - s.active_elapsed_seconds
        if remaining <= 0:
            s.status = 'FAILED'; s.finished_at = now
            s.save(update_fields=['status','finished_at','updated_at'])
            settle_session(s, reason='TIME_EXPIRED')
        else:
            s.status = 'PLAYING'; s.active_since = now
            s.expires_at = now + timedelta(seconds=remaining)
            s.save(update_fields=['status','active_since','expires_at','updated_at'])
    return s

def normalize(text):
    return str(text).strip().casefold()

def check_stage_answer(*, puzzle, submitted_answer):
    """Valida el tipo sin aceptar valores fuera de las opciones configuradas."""
    answer = str(submitted_answer).strip()
    expected = str(puzzle.solution_hash).strip()
    kind = puzzle.type
    if kind == 'NUMBER':
        try:
            return Decimal(answer.replace(',', '.')) == Decimal(expected.replace(',', '.'))
        except InvalidOperation:
            return False
    if kind == 'MULTIPLE_CHOICE':
        options = puzzle.config.get('options', [])
        return answer in options and answer == expected
    if kind == 'SEQUENCE':
        split = lambda v: [normalize(x) for x in re.split(r'[,;|]', v) if x.strip()]
        return split(answer) == split(expected)
    if kind == 'OBJECT':
        objects = puzzle.config.get('objects', [])
        return answer in objects and answer == expected
    if puzzle.config.get('answer_mode') == 'EXACT':
        return answer == expected
    return normalize(answer) == normalize(expected)


@transaction.atomic
def start_session(*,user,escape_room):
    stages=list(Stage.objects.filter(room__escape_room=escape_room).select_related('room').prefetch_related('puzzles').order_by('room__order','order'))
    if not escape_room.is_active or not stages or any(not r.stages.exists() for r in escape_room.rooms.all()):
        raise ValueError('La aventura necesita habitaciones publicadas con fases jugables.')
    for stage in stages:
        puzzles=list(stage.puzzles.all())
        if len(puzzles)!=1:
            raise ValueError('El MVP requiere un puzzle en cada fase.')
        puzzle=puzzles[0]
        if not puzzle.solution_hash or puzzle.solution_hash.startswith('placeholder_'):
            raise ValueError('El contenido contiene soluciones provisionales.')
        if puzzle.config.get('answer_mode','CASE_INSENSITIVE') not in {'EXACT','CASE_INSENSITIVE'}:
            raise ValueError('Modo de comparación no compatible.')
        if puzzle.type=='MULTIPLE_CHOICE' and puzzle.solution_hash not in puzzle.config.get('options',[]):
            raise ValueError('La respuesta debe pertenecer a las opciones.')
        if puzzle.type=='OBJECT' and puzzle.solution_hash not in puzzle.config.get('objects',[]):
            raise ValueError('El objeto correcto debe pertenecer al inventario de opciones.')
    now=timezone.now()
    s=UserEscapeSession.objects.create(user=user,escape_room=escape_room,status='PLAYING',started_at=now,
        expires_at=now+timedelta(seconds=escape_room.time_limit_seconds),active_since=now,current_room=stages[0].room,current_stage=stages[0],
        rules_snapshot={**PREHISTORY_RULES, 'time_limit_seconds':escape_room.time_limit_seconds, 'difficulty':escape_room.difficulty,'version':escape_room.version})
    for room in escape_room.rooms.all():
        first=room.pk==s.current_room_id
        UserRoomProgress.objects.create(session=s,room=room,status='AVAILABLE' if first else 'LOCKED',started_at=now if first else None)
    for stage in stages:
        first=stage.pk==s.current_stage_id
        UserStageProgress.objects.create(session=s,stage=stage,status='AVAILABLE' if first else 'LOCKED',started_at=now if first else None)
    return s

@transaction.atomic
def settle_session(session, *, reason):
    s = UserEscapeSession.objects.select_for_update().get(pk=session.pk)
    if s.status not in {'COMPLETED', 'FAILED', 'ABANDONED'}:
        raise ValueError('La sesión todavía está activa.')

    # Idempotente: si ya existe liquidación, la devolvemos
    existing = EscapeSettlement.objects.filter(session=s).first()
    if existing:
        return existing

    rules = {**PREHISTORY_RULES, **s.rules_snapshot}
    gross = s.stage_progress.aggregate(v=Sum('gross_xp'))['v'] or 0
    penalty = s.hint_usages.aggregate(v=Sum('score_penalty'))['v'] or 0
    penalty += s.puzzle_attempts.filter(is_correct=False).count() * rules['incorrect_penalty']
    # Cada puzzle tiene suelo cero; el bonus temporal no se penaliza.
    per_stage = 0
    for progress in s.stage_progress.select_related('stage'):
        if not progress.is_solved:
            continue
        hint_cost = s.hint_usages.filter(hint__puzzle__stage=progress.stage).aggregate(v=Sum('score_penalty'))['v'] or 0
        wrong = s.puzzle_attempts.filter(puzzle__stage=progress.stage, is_correct=False).count()
        per_stage += max(0, progress.gross_xp - hint_cost - wrong * rules['incorrect_penalty'])
    bonus_xp = 0
    if s.status == 'COMPLETED':
        remaining = max(0, rules['time_limit_seconds'] - elapsed_seconds(s, s.finished_at))
        bonus_xp = int(rules['time_bonus_max'] * remaining / rules['time_limit_seconds'])
    final_total = min(rules['puzzle_points'] * 8 + rules['time_bonus_max'], per_stage + bonus_xp)

    result = EscapeSettlement.objects.create(
        session=s,
        gross_xp=gross,
        penalty_xp=penalty,
        final_xp=final_total,
        bonus_xp=bonus_xp,
        bonus_coins=0,
        reason=reason,
    )

    s.score = final_total
    s.settled_at = timezone.now()
    s.save(update_fields=['score', 'settled_at', 'updated_at'])

    return result

def _expire(s):
    if s.status=='PLAYING' and get_remaining_seconds(s)<=0:
        s.finished_at=timezone.now();s.active_elapsed_seconds=elapsed_seconds(s,s.finished_at);s.active_since=None;s.status='FAILED';s.save(update_fields=['status','finished_at','active_elapsed_seconds','active_since','updated_at'])
        settle_session(s,reason='TIME_EXPIRED')
        return True
    return False

@transaction.atomic
def expire_session_if_needed(session):
    locked=UserEscapeSession.objects.select_for_update().get(pk=session.pk)
    result=_expire(locked);session.refresh_from_db();return result

def _advance(s, stage):
    """Agota TODAS las fases de la sala antes de desbloquear otra sala."""
    now = timezone.now()
    next_stage = stage.room.stages.filter(order__gt=stage.order).order_by('order').first()
    if next_stage is None:
        s.room_progress.filter(room=stage.room).update(
            status='COMPLETED', completed_at=now,
            final_fragment_acquired=stage.room.final_fragment, coins_awarded=0)
        next_room = s.escape_room.rooms.filter(order__gt=stage.room.order).order_by('order').first()
        if next_room:
            next_stage = next_room.stages.order_by('order').first()
            s.room_progress.filter(room=next_room).update(status='AVAILABLE', started_at=now)
    if next_stage:
        s.current_stage = next_stage
        s.current_room = next_stage.room
        s.stage_progress.filter(stage=next_stage).update(status='AVAILABLE', started_at=now)
    else:
        s.active_elapsed_seconds = elapsed_seconds(s, now)
        s.status = 'COMPLETED'
        s.finished_at = now
        s.active_since = None
    s.save()
    if s.status == 'COMPLETED':
        settle_session(s, reason='COMPLETED')

@transaction.atomic
def register_attempt(*,session,puzzle,answer,is_correct=None):
    s=UserEscapeSession.objects.select_for_update().get(pk=session.pk)
    if _expire(s) or s.status!='PLAYING':
        session.refresh_from_db()
        return {'is_correct':False,'completed':False,'failed':True}
    if puzzle.stage_id!=s.current_stage_id:
        raise ValueError('La fase ha cambiado. Revisa la prueba actual.')
    if not isinstance(answer, str) or not answer.strip() or len(answer) > 1000:
        raise ValueError('Respuesta inválida o demasiado larga.')
    # Adventure-specific world prerequisites are authoritative server-side.
    required = puzzle.config.get("required_world", {})
    if required:
        from .models import EscapeWorldState
        actual = dict(EscapeWorldState.objects.filter(
            session=s, interactable__room__escape_room=s.escape_room,
            interactable__key__in=required.keys(),
        ).values_list("interactable__key", "state"))
        if any(actual.get(key) != state for key, state in required.items()):
            raise ValueError("Antes debes activar los mecanismos necesarios de la sala.")
    correct=check_stage_answer(puzzle=puzzle,submitted_answer=answer)
    number=s.puzzle_attempts.filter(puzzle=puzzle).count()+1
    PuzzleAttempt.objects.create(session=s,puzzle=puzzle,player=s.user,attempt_no=number,answer={'value':answer},is_correct=correct)
    progress=s.stage_progress.get(stage=puzzle.stage)
    progress.attempts+=1;progress.status='IN_PROGRESS'
    if correct:
        progress.is_solved=True;progress.status='COMPLETED';progress.completed_at=timezone.now()
        progress.fragment_acquired=puzzle.stage.fragment;progress.gross_xp=puzzle.points;progress.net_xp=puzzle.points
        progress.time_spent_seconds=max(0,int((progress.completed_at-(progress.started_at or s.started_at)).total_seconds()))
        s.score+=puzzle.points
    progress.save()
    if correct:_advance(s,puzzle.stage)
    elif puzzle.max_attempts and number>=puzzle.max_attempts:
        s.finished_at=timezone.now();s.active_elapsed_seconds=elapsed_seconds(s,s.finished_at);s.active_since=None;s.status='FAILED';s.save()
        progress.status='FAILED';progress.save(update_fields=['status'])
        settle_session(s,reason='FAILED')
    session.refresh_from_db()
    return {'is_correct':correct,'completed':session.status=='COMPLETED','failed':session.status=='FAILED'}

def get_available_hint(session, stage):
    """Devuelve la siguiente pista disponible para la fase actual.
    
    MVP: ignora `coin_price` (sistema de monedas pendiente). Las
    penalizaciones de tiempo y puntos sí se aplican al usarla.
    """
    used_ids = list(session.hint_usages.values_list('hint_id', flat=True))

    # Primero intenta pistas de este puzzle; si no, pistas de la habitación
    hint = (Hint.objects
            .filter(puzzle__stage=stage)
            .exclude(pk__in=used_ids)
            .order_by('order')
            .first()
            or Hint.objects
            .filter(room=stage.room)
            .exclude(pk__in=used_ids)
            .order_by('order')
            .first())

    if hint is None:
        return None

    start = session.stage_progress.get(stage=stage).started_at or session.started_at
    # Pauses must not advance hint unlock timers.
    active_age = max(0, elapsed_seconds(session) - max(0, (start - session.started_at).total_seconds()))
    if active_age < hint.unlock_after_seconds:
        return None

    return hint

@transaction.atomic
def use_hint(session,hint):
    s=UserEscapeSession.objects.select_for_update().get(pk=session.pk)
    if _expire(s) or s.status!='PLAYING':
        session.refresh_from_db();return False
    candidate=get_available_hint(s,s.current_stage)
    if candidate is None or candidate.pk!=hint.pk:return False
    HintUsage.objects.create(session=s,hint=hint,player=s.user,score_penalty=hint.penalty_points,time_penalty=hint.penalty_seconds,coins_charged=0)
    # Las pistas de esta aventura penalizan puntos, no segundos.
    s.save(update_fields=['updated_at'])
    _expire(s);session.refresh_from_db();return True

@transaction.atomic
def abandon_session(session):
    s = UserEscapeSession.objects.select_for_update().get(pk=session.pk)
    if not _expire(s) and s.status in {'PLAYING', 'PAUSED'}:
        s.finished_at = timezone.now()
        s.active_elapsed_seconds = elapsed_seconds(s, s.finished_at)
        s.active_since = None
        s.status = 'ABANDONED'
        s.save(update_fields=['status', 'finished_at', 'active_elapsed_seconds', 'active_since', 'updated_at'])
        settle_session(s, reason='ABANDONED')
    return s

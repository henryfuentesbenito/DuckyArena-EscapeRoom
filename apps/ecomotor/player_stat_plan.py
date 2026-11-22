"""Política de estadísticas 45+5 históricas / 50 libres en especialización.

Los vectores históricos son PROVISIONALES y provienen de la política local existente.
No se aplican a Core. Las operaciones se serializan en la transacción del perfil.
"""
from django.db import transaction
from django.db.models import F
from .models import CharacterStats, EvolutionStage, PlayerStatPlan, STAT_ATTRIBUTES
from .target_stats_historical_policy import historical_epoch_bases_45

STAGE_NAMES = ("Prehistoria", "Grecia", "Roma", "Medieval", "Renacimiento", "Revolución Industrial", "Siglo XX")
CODE_TO_FIELD = {"ATK":"atk", "DEF":"def_stat", "LOG":"log_stat", "VEL":"vel", "INT":"int_stat", "ESP":"spe"}
MAX_SPECIALIZATION_STAT = 12


def _base(stage_code, using):
    ordinal = EvolutionStage.objects.using(using).get(code=stage_code).ordinal
    return {CODE_TO_FIELD[k]:v for k,v in historical_epoch_bases_45(STAGE_NAMES[ordinal-1])}


def _zero():
    return {key:0 for key in STAT_ATTRIBUTES}


def sync_player_stats(profile):
    """Sincroniza al inicializar, evolucionar o cambiar de especialización."""
    using = profile._state.db or "default"
    with transaction.atomic(using=using):
        from apps.users.models import UserProfileEcomotor
        current = UserProfileEcomotor.objects.using(using).select_for_update().get(pk=profile.pk)
        stats = CharacterStats.objects.using(using).select_for_update().filter(profile=current).first()
        if stats is None:
            return None
        plan, created = PlayerStatPlan.objects.using(using).select_for_update().get_or_create(
            profile=current, defaults={"stage_code":current.current_stage_code, "active_branch":current.active_specialization_code or ""})
        branch = current.active_specialization_code or ""
        changed = created or plan.stage_code != current.current_stage_code or plan.active_branch != branch
        if not changed:
            # XP antigua puede otorgar puntos por nivel: esta política fija 5/50.
            expected_values = (plan.allocations if branch else
                               {key:_base(current.current_stage_code, using)[key] + plan.allocations.get(key,0) for key in STAT_ATTRIBUTES})
            expected_available = (50 if branch else 5) - sum(plan.allocations.values())
            if any(getattr(stats,key) != expected_values[key] for key in STAT_ATTRIBUTES) or stats.available_points != expected_available:
                for key in STAT_ATTRIBUTES:
                    setattr(stats,key,expected_values[key])
                stats.available_points = expected_available
                stats.save(using=using, update_fields=[*STAT_ATTRIBUTES, "available_points"])
            return plan
        if branch:
            allocations = plan.branch_allocations.get(branch, _zero())
            if not isinstance(allocations, dict) or any(type(allocations.get(k)) is not int or not 0 <= allocations[k] <= 12 for k in STAT_ATTRIBUTES) or sum(allocations.values()) > 50:
                allocations = _zero()
            if not plan.active_branch or created:
                plan.specialization_notice_pending = True
            plan.active_branch = branch
            plan.allocations = allocations
            values = allocations
            available = 50 - sum(allocations.values())
        else:
            plan.active_branch = ""
            plan.allocations = _zero()
            values = _base(current.current_stage_code, using)
            available = 5
        plan.stage_code = current.current_stage_code
        plan.save(using=using)
        for field in STAT_ATTRIBUTES:
            setattr(stats, field, values[field])
        stats.available_points = available
        stats.save(using=using, update_fields=[*STAT_ATTRIBUTES, "available_points"])
        return plan


def distribute_points(profile, attribute, points):
    if attribute not in STAT_ATTRIBUTES or type(points) is not int or points < 1:
        raise ValueError("Estadística o puntos inválidos")
    using = profile._state.db or "default"
    with transaction.atomic(using=using):
        plan = sync_player_stats(profile)
        if plan is None:
            raise ValueError("No existen estadísticas del jugador")
        stats = CharacterStats.objects.using(using).select_for_update().get(profile_id=profile.pk)
        if points > stats.available_points:
            raise ValueError("No tienes suficientes puntos disponibles")
        if plan.active_branch and getattr(stats, attribute) + points > MAX_SPECIALIZATION_STAT:
            raise ValueError("Máximo 12 puntos por estadística en especialización")
        setattr(stats, attribute, getattr(stats, attribute) + points)
        stats.available_points -= points
        stats.save(using=using, update_fields=[attribute, "available_points"])
        allocations = dict(plan.allocations)
        allocations[attribute] = allocations.get(attribute, 0) + points
        plan.allocations = allocations
        if plan.active_branch:
            branches = dict(plan.branch_allocations)
            branches[plan.active_branch] = allocations
            plan.branch_allocations = branches
        plan.save(using=using, update_fields=["allocations", "branch_allocations"])
        return stats


def redistribute_points(profile, allocations):
    """Reemplaza el reparto libre completo, incluso sin saldo disponible.

    Los 45 puntos históricos son inmutables; cada especialización conserva
    su propio reparto de hasta 50 puntos. Todo se guarda atómicamente.
    """
    if not isinstance(allocations, dict) or set(allocations) != set(STAT_ATTRIBUTES):
        raise ValueError("Debes indicar las seis estadísticas")
    if any(type(value) is not int or value < 0 for value in allocations.values()):
        raise ValueError("Los puntos deben ser enteros no negativos")
    using = profile._state.db or "default"
    with transaction.atomic(using=using):
        from apps.users.models import UserProfileEcomotor
        current = UserProfileEcomotor.objects.using(using).select_for_update().get(pk=profile.pk)
        plan = sync_player_stats(current)
        if plan is None:
            raise ValueError("No existen estadísticas del jugador")
        plan = PlayerStatPlan.objects.using(using).select_for_update().get(pk=plan.pk)
        stats = CharacterStats.objects.using(using).select_for_update().get(profile=current)
        is_specialization = bool(current.active_specialization_code)
        budget = 50 if is_specialization else 5
        if sum(allocations.values()) > budget:
            raise ValueError(f"No puedes repartir más de {budget} puntos")
        if is_specialization and any(value > MAX_SPECIALIZATION_STAT for value in allocations.values()):
            raise ValueError("Máximo 12 puntos por estadística en especialización")
        base = _zero() if is_specialization else _base(current.current_stage_code, using)
        for key in STAT_ATTRIBUTES:
            setattr(stats, key, base[key] + allocations[key])
        stats.available_points = budget - sum(allocations.values())
        stats.save(using=using, update_fields=[*STAT_ATTRIBUTES, "available_points"])
        plan.allocations = dict(allocations)
        if is_specialization:
            branches = dict(plan.branch_allocations)
            branches[current.active_specialization_code] = dict(allocations)
            plan.branch_allocations = branches
        plan.save(using=using, update_fields=["allocations", "branch_allocations"])
        return stats


def consume_specialization_notice(profile):
    with transaction.atomic():
        changed = PlayerStatPlan.objects.filter(profile=profile, specialization_notice_pending=True).update(specialization_notice_pending=False)
        return bool(changed)

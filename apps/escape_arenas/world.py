"""Authoritative world interactions. No browser-supplied item ownership or state."""
from django.db import transaction
from .models import (UserEscapeSession, EscapeInteractable, EscapeItemDefinition,
                     EscapeSessionItem, EscapeWorldState)
from .services import _expire


class WorldActionError(ValueError):
    pass


def public_world(session):
    room = session.current_room
    if not room:
        return {"inventory": [], "interactables": []}
    inventory = [{"key": row.item.key, "name": row.item.name, "quantity": row.quantity,
                  "asset_key": row.item.asset_key} for row in session.world_items.select_related("item").filter(quantity__gt=0)]
    states = {row.interactable_id: row.state for row in session.world_states.all()}
    interactables = [{"key": obj.key, "label": obj.label, "asset_key": obj.asset_key,
                      "x": obj.x, "y": obj.y, "state": states.get(obj.pk, "idle"),
                      "actions": list(obj.actions.keys())}
                     for obj in room.interactables.all()]
    return {"inventory": inventory, "interactables": interactables}


@transaction.atomic
def interact(*, session, target_key, action, item_key=None):
    s = UserEscapeSession.objects.select_for_update().get(pk=session.pk)
    if _expire(s) or s.status != "PLAYING" or not s.current_room_id:
        raise WorldActionError("La partida no está activa.")
    target = EscapeInteractable.objects.filter(room_id=s.current_room_id, key=target_key).first()
    if not target or action not in target.actions:
        raise WorldActionError("Interacción no disponible.")
    policy = target.actions[action]
    if not isinstance(policy, dict):
        raise WorldActionError("Configuración de interacción inválida.")
    world, _ = EscapeWorldState.objects.get_or_create(session=s, interactable=target)
    if action == "inspect":
        return {"message": target.label, "world": public_world(s)}
    if action == "collect":
        if world.state == "collected":
            return {"message": "Objeto ya recogido.", "world": public_world(s)}
        key = policy.get("item")
        definition = EscapeItemDefinition.objects.filter(escape_room=s.escape_room, key=key).first()
        if not definition:
            raise WorldActionError("Objeto no configurado.")
        row, _ = EscapeSessionItem.objects.get_or_create(session=s, item=definition, defaults={"quantity": 0})
        row.quantity += 1
        row.save(update_fields=["quantity"])
        world.state = "collected"
    elif action == "use":
        required = policy.get("requires_item")
        if not required or required != item_key:
            raise WorldActionError("Selecciona el objeto adecuado.")
        if world.state == policy.get("next_state", "activated"):
            return {"message": "Mecanismo ya activado.", "world": public_world(s)}
        row = EscapeSessionItem.objects.select_for_update().filter(
            session=s, item__escape_room=s.escape_room, item__key=required, quantity__gt=0).first()
        if not row:
            raise WorldActionError("No tienes ese objeto.")
        if policy.get("consume", False):
            row.quantity -= 1
            row.save(update_fields=["quantity"])
        world.state = policy.get("next_state", "activated")
    else:
        raise WorldActionError("Acción no implementada.")
    world.save(update_fields=["state"])
    return {"message": policy.get("message", "Acción realizada."), "world": public_world(s)}

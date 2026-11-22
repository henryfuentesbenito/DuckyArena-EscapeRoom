"""Read-only bridge to Team 5 official Ducky and outfit image registry."""
from apps.duckies.models import Ducky
from apps.portal.image_registry import ducky_image

def public_ducky(user):
    ducky = Ducky.objects.select_related("selected_outfit").filter(user=user).first()
    if ducky is None:
        return {"exists": False, "image_url": None, "name": "Ducky no creado", "outfit": None}
    outfit = ducky.selected_outfit
    return {
        "exists": True,
        "image_url": ducky_image(ducky),
        "name": "Mi Ducky",
        "outfit": outfit.name if outfit else None,
        "sex": ducky.sex,
    }

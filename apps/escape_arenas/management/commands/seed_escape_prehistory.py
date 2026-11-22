"""Versioned prehistoric adventure; leaves the legacy six-phase demo untouched."""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.escape_arenas.models import (EscapeRoom, Room, Stage, Puzzle, Hint,
    EscapeItemDefinition, EscapeInteractable)

SLUG = "laboratorio-tiempo-prehistoria-v1"
ROOMS = [
    ("La cueva del descubrimiento", "Cristales, runas y una salida sellada"),
    ("El taller ancestral", "Repara la rueda cronológica y la terminal"),
    ("El portal temporal", "Estabiliza el núcleo y abre el portal"),
]
# Structured, bounded challenges. These are initial playtest rules, not final scoring policy.
CHALLENGES = [
    (0,"Energía perdida", "Ordena: recoger, colocar, activar, verificar", "SEQUENCE", "recoger,colocar,activar,verificar", {"required_world":{"altar":"lit"}}),
    (0,"Circuito ancestral", "AND: A=1, B=1. OR: C=0, D=1. ¿(A AND B) AND (C OR D)? (1/0)", "NUMBER", "1", {}),
    (0,"Acceso restringido", "energia=4, cristales=3. Calcula energia*cristales+2", "NUMBER", "14", {}),
    (1,"Cronología rota", "Ordena: recuperar, ensamblar, calibrar, encender", "SEQUENCE", "recuperar,ensamblar,calibrar,encender", {"required_world":{"workshop-machine":"repaired"}}),
    (1,"Terminal bloqueada", "Corrige la condición: si energia = 5, ¿qué operador compara igualdad?", "MULTIPLE_CHOICE", "==", {"options":["=","==","+="]}),
    (1,"Calibración temporal", "Un bucle suma 2 unidades durante 4 iteraciones. ¿Resultado?", "NUMBER", "8", {}),
    (2,"Núcleo inestable", "Si temperatura > 10, activar refrigeración; en otro caso, mantener. Temperatura=12", "MULTIPLE_CHOICE", "refrigeración", {"options":["refrigeración","mantener"], "required_world":{"portal-core":"stabilized"}}),
    (2,"Apertura del portal", "Ordena: comprobar, estabilizar, repetir, abrir", "SEQUENCE", "comprobar,estabilizar,repetir,abrir", {}),
]

class Command(BaseCommand):
    help = "Crea El laboratorio del tiempo v1 (3 salas, 8 desafíos) sin tocar la demo anterior."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        EscapeRoom.objects.filter(slug="escape-demo-seis-fases").update(is_active=False)
        if EscapeRoom.objects.filter(slug=SLUG).exists():
            self.stdout.write("La aventura v1 ya existe; se preserva su contenido y partidas.")
            return
        adventure = EscapeRoom.objects.create(
            slug=SLUG, name="El laboratorio del tiempo — Prehistoria",
            description="Escapa del laboratorio temporal resolviendo ocho mecanismos.",
            estimated_duration=25, time_limit_seconds=1500, final_solution_hash="",
            is_active=True, difficulty="EASY", theme="LAB", era=1)
        rooms=[]
        for index,(name,desc) in enumerate(ROOMS,1):
            rooms.append(Room.objects.create(escape_room=adventure,name=name,
                description=desc,order=index,door_solution_hash="",final_fragment=""))
        for index,(room_index,name,description,kind,answer,config) in enumerate(CHALLENGES,1):
            room=rooms[room_index]
            order=sum(1 for challenge in CHALLENGES[:index] if challenge[0]==room_index)
            stage=Stage.objects.create(room=room,name=name,description=description,
                order=order,type="PUZZLE")
            if kind == "SEQUENCE":
                config = {**config, "sequence_items": list(reversed(answer.split(",")))}
            puzzle=Puzzle.objects.create(stage=stage,title=name,description=description,
                type=kind,config=config,solution_hash=answer,max_attempts=None,
                points=100,order=1)
            for level, hint in enumerate((
                "Identifica primero los datos y el objetivo.",
                "Divide el problema en pasos y comprueba el orden o la condición.",
                "Utiliza las operaciones descritas y comprueba cada paso antes de responder.",
            ),1):
                Hint.objects.create(puzzle=puzzle,text=hint,order=level,
                    penalty_points=[10,20,30][level-1],penalty_seconds=0,coin_price=0)
        crystal=EscapeItemDefinition.objects.create(escape_room=adventure,key="energy-crystal",
            name="Cristal energético",description="Alimenta el altar",asset_key="prehistoric.cave.crystal")
        EscapeInteractable.objects.create(room=rooms[0],key="cave-crystal",label="Cristal energético",
            x=.27,y=.67,asset_key="prehistoric.cave.crystal",
            actions={"inspect":{},"collect":{"item":crystal.key,"message":"Cristal recogido"}})
        EscapeInteractable.objects.create(room=rooms[0],key="altar",label="Altar energético",
            x=.52,y=.58,asset_key="prehistoric.cave.altar",
            actions={"inspect":{},"use":{"requires_item":crystal.key,"consume":True,
                "next_state":"lit","message":"El altar comienza a brillar"}})
        coil=EscapeItemDefinition.objects.create(escape_room=adventure,key="temporal-coil",name="Bobina temporal",description="Repara el taller",asset_key="prehistoric.workshop.coil")
        EscapeInteractable.objects.create(room=rooms[1],key="workshop-coil",label="Bobina temporal",x=.28,y=.62,asset_key="prehistoric.workshop.coil",actions={"inspect":{},"collect":{"item":coil.key,"message":"Bobina recogida"}})
        EscapeInteractable.objects.create(room=rooms[1],key="workshop-machine",label="Máquina cronológica",x=.64,y=.55,asset_key="prehistoric.workshop.machine",actions={"inspect":{},"use":{"requires_item":coil.key,"consume":True,"next_state":"repaired","message":"Máquina reparada"}})
        shard=EscapeItemDefinition.objects.create(escape_room=adventure,key="portal-shard",name="Fragmento del portal",description="Estabiliza el núcleo",asset_key="prehistoric.portal.shard")
        EscapeInteractable.objects.create(room=rooms[2],key="portal-shard",label="Fragmento temporal",x=.26,y=.63,asset_key="prehistoric.portal.shard",actions={"inspect":{},"collect":{"item":shard.key,"message":"Fragmento recogido"}})
        EscapeInteractable.objects.create(room=rooms[2],key="portal-core",label="Núcleo del portal",x=.64,y=.55,asset_key="prehistoric.portal.core",actions={"inspect":{},"use":{"requires_item":shard.key,"consume":True,"next_state":"stabilized","message":"Núcleo estabilizado"}})
        self.stdout.write(self.style.SUCCESS("Aventura v1 creada: 3 salas, 8 desafíos, 24 pistas y mecanismos persistentes."))

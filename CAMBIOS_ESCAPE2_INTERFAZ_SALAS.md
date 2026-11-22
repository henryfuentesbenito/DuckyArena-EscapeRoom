# Adaptación Escape 2 — Salas y pergaminos

## Implementado
- Fondos cueva, taller y portal según `room.order` de Django.
- MiniDucky original direccional con WASD/flechas/clic; movimiento visual local.
- Pergamino de desafíos y controles visuales de circuito, código rúnico, terminal, bucle y núcleo.
- Secuencias reordenables; API real Django de respuestas, pistas, inventario, interacciones y temporizador intacta.
- Sin lógica simulada ni recompensas en localStorage.

## Límites
- Las reglas y respuestas del seed existente no se han modificado; varios mecanismos aún son simplificaciones de los ocho minijuegos definitivos.
- No hay colocación de tres módulos independientes en el núcleo, ni arrastre físico de piezas; las secuencias usan flechas.
- El movimiento del MiniDucky es visual; los hotspots se activan con clic.
- Sin pruebas end-to-end en navegador ni migraciones ejecutadas.

## Verificación
- `node --check` de RoomScene.js y puzzle-modal.js: correcto.
- Compilación Python: correcta.
- `manage.py check` no se pudo ejecutar por ausencia de Django en este entorno.

## Arranque
Desde la carpeta con `manage.py`:
```
python -m pip install -r requirements.txt
python manage.py check --settings=config.settings_team5_local
python manage.py migrate --settings=config.settings_team5_local
python manage.py seed_escape_prehistory --settings=config.settings_team5_local
python manage.py runserver --settings=config.settings_team5_local
```
Entra por Arena > Escape. El seed es conservador si la aventura ya existe.

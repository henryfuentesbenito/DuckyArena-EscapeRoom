# Integración DuckyEscape en Equipo 5 — versión para pruebas

## Alcance
- Aplicación `apps.escape_arenas` integrada en el Django de Equipo 5, con sus modelos, migraciones, servicios, editor, plantillas, Phaser y tests.
- Acceso desde la tarjeta Escape de la Arena, rutas bajo `/escape/` y autenticación compartida Django.
- No se han importado `core`, `apps.users`, `config`, base de datos ni middleware del proyecto Escape independiente.
- El resultado de Escape **es puntuación local**. No se acreditan XP de Ecomotor ni DuckyCoins de Bank hasta aprobar política de recompensas y crear adaptador idempotente.
- La UI de Escape conserva temporalmente su estilo propio; enlaza con la Arena principal. El avatar oficial del Ducky aún no se muestra dentro de Phaser.

## Arranque Windows (desde carpeta de manage.py)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd training_frontend
npm ci
npm run build
cd ..
python manage.py check --settings=config.settings_team5_local
python manage.py migrate --settings=config.settings_team5_local
python manage.py test apps.escape_arenas --settings=config.settings_team5_local
python manage.py runserver --settings=config.settings_team5_local
```

## Demo Escape
```powershell
python manage.py seed_escape --settings=config.settings_team5_local
```
Comprobar `python manage.py seed_escape --help` para los parámetros reales.

## Validación pendiente
- Partida completa en navegador con la demo, temporizador, pistas y liquidación local.
- Pruebas conjuntas Training/Quiz/Equipo 5 en Windows.
- Verificar assets Phaser con conexión a CDN; para despliegue se recomienda alojarlo localmente.
- Acordar política de XP/monedas y adaptador oficial antes de acreditar recompensas.

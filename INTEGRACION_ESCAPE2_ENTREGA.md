# Integración Escape 2 — entrega para pruebas

## Procedencia
- Base: `DuckyArena_Equipo5_Training_Quiz_Escape_Integracion_Local_PARA_PRUEBAS(1).zip`.
- Se sustituyó `apps/escape_arenas/` por el contenido de `escape_arenas(1).zip`.
- Se conservaron las demás aplicaciones y la configuración del proyecto base.

## Comprobaciones efectuadas
- Los módulos Python de Escape compilan sintácticamente.
- `config/settings.py` ya registra `apps.escape_arenas.apps.EscapeArenasConfig`.
- `config/urls.py` ya incluye `/escape/`.
- El proveedor oficial `apps.portal.image_registry.ducky_image` existe.
- Las migraciones `0001` a `0004` coinciden con las de la base; la entrega añade `0005` a `0007`.

## Límites de validación
No se han podido ejecutar `manage.py check`, migraciones, pruebas Django ni navegador porque las dependencias Django no están instaladas en este entorno y la instalación no tiene acceso a la red. Esta entrega no está certificada para producción.

El archivo `apps/escape_arenas/HITO4_CAMBIOS_INTEGRACION.md` declara pendientes las pruebas de los ocho minijuegos, los tres finales y la interfaz responsive.

## Arranque local (PowerShell)
Desde la carpeta que contiene `manage.py`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py check --settings=config.settings_team5_local
python manage.py migrate --settings=config.settings_team5_local
python manage.py seed_escape_prehistory --settings=config.settings_team5_local
python manage.py runserver --settings=config.settings_team5_local
```

Entrar en `/escape/game/` después de iniciar sesión, o mediante Arena. Antes de migrar una base de datos existente, hacer copia de seguridad y revisar `showmigrations` y `migrate --plan`.

## Advertencia funcional
La aventura registra tres salas y ocho desafíos, pero varios son respuestas numéricas, opciones o secuencias en un modal, no los ocho mecanismos visuales completamente interactivos previstos. La integración técnica de la carpeta no implica que el videojuego esté finalizado.

# Cambios de estadísticas, equipamiento y Arena — integración local

## Implementación

- 7 épocas: vectores históricos provisionales de 45 puntos derivados de la política existente `target_stats_historical_policy.py`; 5 puntos asignables en cada época, sin acumulación. Las transiciones de XP regeneran los puntos de la época siguiente.
- Especializaciones: 50 puntos libres, máximo 12 por atributo; distribución independiente guardada por especialización. Los puntos no usados no impiden jugar. Mensaje de especialización de una sola visualización.
- Seis ranuras físicas: ataque 1/2/3, defensa 1/2/3. Se desbloquean alternativamente a partir de la segunda época, hasta la séptima. Los artículos conservan sus variantes visuales según la vestimenta activa.
- Arena: tarjetas responsive 2x2 para Training, Quiz, Escape y Clash. Training es el único enlace funcional; los otros están marcados como próximos.
- La demo local, Bank, Training y Core no se sustituyen.

## Arranque

```powershell
python -m pip install -r requirements.txt
python manage.py migrate --settings=config.settings_team5_local
python manage.py team5_setup_local --settings=config.settings_team5_local
python manage.py seed_shop_catalog --settings=config.settings_team5_local
python manage.py seed_logical_exercises --settings=config.settings_team5_local
python manage.py runserver --settings=config.settings_team5_local
```

Para el modo normal, usar `--settings=config.settings` o `python manage.py runserver` y aplicar las migraciones correspondientes. El frontend de Training requiere compilación (`cd training_frontend; npm ci; npm run build`).

## Límites de validación

Se comprobó la sintaxis de los módulos Python y la integridad del ZIP. No se ejecutaron Django, migraciones, tests ni React porque las dependencias no están instaladas y no se pueden descargar desde este entorno. Los valores históricos son provisionales, no aprobados por Core. Se recomienda una copia de seguridad de la BD antes de migrar y una prueba integral local antes de utilizar el ZIP como demo definitiva.

## Nota de compatibilidad

El sistema anterior `stat_allocation.py` conserva su API y eventos para auditoría, pero la interfaz nueva usa `player_stat_plan.py`. Las asignaciones anteriores no se trasladan automáticamente; el nuevo plan se inicia al primer uso y la transición de época reinicia la distribución. Las ranuras genéricas heredadas (`ATTACK`, `DEFENSE`) se muestran como compatibilidad visual; para migrar objetos ya equipados se debe reequiparlos mediante la interfaz.

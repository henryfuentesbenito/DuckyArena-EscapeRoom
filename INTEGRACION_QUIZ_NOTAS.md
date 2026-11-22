# Integración Quiz — Equipo 5

Se han incorporado las aplicaciones `quizzes` y `quiz_games` del ZIP DuckyArena-developer al proyecto principal, manteniendo Training. Quiz está accesible desde Arena.

## Ejecución

```powershell
python -m pip install -r requirements.txt
python manage.py migrate --settings=config.settings_team5_local
python manage.py runserver --settings=config.settings_team5_local
```

Las rutas HTTP de Quiz están bajo `/arena/quiz/quizzes/` y `/arena/quiz/games/`. WebSocket: `/ws/quiz/game/<PIN>/`. El ASGI unificado usa Channels y Daphne.

## Política local de recompensas (provisional)

5 XP y 1 DuckyCoin por respuesta correcta validada y distinta, únicamente al finalizar la partida. No se utilizan puntos de velocidad/racha como moneda. Operaciones con claves idempotentes por partida y jugador; se utilizan Ecomotor y Bank. Core no está integrado.

## Limitaciones

- No se ha ejecutado el conjunto completo de pruebas Django en este entorno; comprobar migraciones y flujo real antes de merge.
- `InMemoryChannelLayer` solo admite un proceso ASGI; para producción, utilizar Redis.
- Las pantallas Quiz mantienen la estética propia del equipo Quiz, separada visualmente del panel Team 5.
- Los avatares de Quiz son independientes de Duckies y aún requieren unificación visual.
- Redistribución ilimitada de estadísticas pendiente de implementar y validar en Ecomotor.
- Recompensas sujetas a aprobación de la política oficial de XP/monedas.

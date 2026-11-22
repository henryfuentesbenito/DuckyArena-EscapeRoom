# Integración: redistribución y avatar de Quiz

- Dashboard: botón permanente «Redistribuir puntos», seis controles +/−, contador en vivo y guardado POST CSRF.
- Backend: `redistribute_points` reemplaza la distribución completa dentro de una transacción; 45 puntos base históricos inalterados + hasta 5 libres; especialización hasta 50 libres y máximo 12 por estadística. Permite reasignar aun con saldo cero.
- Quiz: `render_ducky_avatar` utiliza la imagen del Ducky oficial y vestimenta seleccionada del usuario; las respuestas JSON de la sala incluyen `avatar.image_url` y el renderizador JavaScript la utiliza. El estudio de avatar del lobby se sustituye por vista del Ducky y acceso al vestuario de Equipo 5.
- Endpoint HTTP de modificación de avatar legado devuelve 403; mensajes WebSocket de modificación rechazados.
- Daphne se ha movido antes de `django.contrib.staticfiles`.

## Verificación local pendiente
Ejecutar `python manage.py check --settings=config.settings_team5_local`, `migrate` y tests con dependencias instaladas. Probar cambio de vestimenta desde Equipo 5 y actualización de lobby/leaderboard de Quiz.

## Nota
La implementación no se ha validado mediante pruebas funcionales en este entorno. No utilizar en producción sin revisar transacciones y migraciones.

# Adaptación visual parcial — 20 noviembre 2026

- Entrada Arena → Escape sigue abriendo `/escape/game/`.
- Hub Phaser rediseñado con tarjetas ilustradas, tipografía temática y fondo de cueva.
- Se conserva el MiniDucky ya existente, sus cuatro sprites y movimiento.
- Se incorporan los tres fondos del ZIP del usuario a `static/escape_arenas/img/escenarios/`.
- El ZIP aportado es una demo frontend: **no** se ha conectado su lógica simulada de puntos, pistas, pausa e inventario a Django; hacerlo reemplazaría incorrectamente la autoridad del servidor.
- Las tarjetas de Cárcel y Colegio siguen deshabilitadas si la API indica que no hay aventuras.
- Pendiente de segunda fase: adaptar la interfaz de sala, los pergaminos y las interacciones del ZIP a las vistas y endpoints Django actuales. No se declara completada esa parte.
- No se han ejecutado pruebas de navegador ni tests Django en este entorno.

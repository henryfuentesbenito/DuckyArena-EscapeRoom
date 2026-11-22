# DuckyArena Equipo 5 + Training — entrega integrada local

## Alcance

El proyecto Django de Equipo 5 es la aplicación principal. Arena incluye Training y reserva Quiz, Escape y Clash para integraciones posteriores. Training valida ejercicios e intentos; Equipo 5 gestiona XP histórica, XP de especialización, vestuario y DuckyCoins. Core no es necesario para esta demo. **No es un despliegue de producción.**

## Windows 10/11 — instalación desde cero

1. Instala Python compatible, Node.js y npm.
2. Descomprime el ZIP en una ruta local sin restricciones.
3. Ejecuta `ARRANCAR_DEMO_TRAINING_WINDOWS.bat`. Requiere conexión a internet la primera vez para instalar dependencias.
4. Si el navegador no inicia sesión automáticamente, abre `http://127.0.0.1:8000/accounts/login/`.
5. Crea un usuario de prueba con `python manage.py createsuperuser --settings=config.settings_team5_local` o desde el registro normal, y crea su Ducky con la interfaz.
6. Accede a Arena → Training. Los juegos del ciclo diario necesitan el seed local y el catálogo sintético habilitado.

## Manual

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DJANGO_SETTINGS_MODULE='config.settings_team5_local'
python manage.py check
python manage.py migrate
python manage.py team5_setup_local
python manage.py seed_logical_exercises
cd training_frontend
npm ci
npm run build
cd ..
python manage.py runserver
```

## Arquitectura de recompensas

- Cada respuesta se valida en Django, se registra como `TrainingAttempt` y crea una `TrainingRewardDelivery` única.
- La concesión se realiza en `apps.integrations.training_rewards.training_reward_handler` con una transacción local.
- Antes de especializarse, XP histórica por `grant_xp_and_sync_outfit`.
- Con especialización activa, XP en la rama seleccionada mediante `grant_specialization_xp`, con evento idempotente `SpecializationXPEvent`. No se inventan umbrales de rango ni recompensas oficiales de Core.
- Bank concede una moneda solo cuando corresponde a la primera finalización correcta diaria del ejercicio; deduplicación mediante operación persistente.
- La configuración `config.settings_team5_local` utiliza una base SQLite separada y habilita contenido provisional **solo para demo**. El catálogo original permanece intacto.
- Los controles manuales siguen aislados en `devtools/team5_local`, nunca en la UI normal.

## Pruebas

```powershell
python manage.py test apps.training apps.ecomotor.test_training_specialization_xp --settings=config.settings_team5_local
```

Prueba manual: registrar usuario, crear Ducky, acceder a Training, acertar, comprobar XP/Bank, reintentar la misma operación y comprobar que no duplica. Cambiar a especialización cuando corresponda y verificar que la XP se asigna a la rama activa.

## Limitaciones y verificación

En el entorno de preparación del ZIP se verificó la sintaxis de Python, pero **no se pudieron ejecutar Django, migraciones, tests ni `npm run build`**, porque faltan paquetes y no hay acceso al registro de dependencias. Por ello, no debe declararse la integración probada hasta ejecutar las instrucciones anteriores en un entorno con dependencias instaladas. Las mecánicas de Training se conservan del repositorio suministrado; el contenido provisional sigue sin aprobación pedagógica.

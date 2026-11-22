@echo off
setlocal
cd /d "%~dp0"
set DJANGO_SETTINGS_MODULE=config.settings_team5_local
if not exist .venv\Scripts\python.exe (
  py -m venv .venv
)
.venv\Scripts\python.exe -m pip install -r requirements.txt || goto :error
.venv\Scripts\python.exe manage.py check || goto :error
.venv\Scripts\python.exe manage.py migrate || goto :error
.venv\Scripts\python.exe manage.py team5_setup_local || goto :error
.venv\Scripts\python.exe manage.py seed_logical_exercises || goto :error
if not exist apps\portal\static\training_build\index.html (
  pushd training_frontend
  call npm ci || goto :error
  call npm run build || goto :error
  popd
)
start "DuckyArena Equipo5 Training" http://127.0.0.1:8000/accounts/login/
.venv\Scripts\python.exe manage.py runserver
exit /b 0
:error
echo ERROR: Revisa la instalacion, las migraciones o la compilacion del frontend.
pause
exit /b 1

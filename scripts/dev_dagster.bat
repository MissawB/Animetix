@echo off
set DAGSTER_HOME=%CD%\pipeline
set PYTHONUTF8=1
if not exist "pipeline\.dagster_home" mkdir "pipeline\.dagster_home"
echo 🚀 Lancement de Dagster (UTF-8 activé) avec DAGSTER_HOME fixé sur %DAGSTER_HOME%
dagster dev -f pipeline/dagster_app.py

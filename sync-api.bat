@echo off
echo [1/3] Extraction du schema OpenAPI depuis Django...
python src\backend\manage.py spectacular --file schema.yaml --quiet

if %ERRORLEVEL% NEQ 0 (
    echo Erreur lors de l'extraction du schema.
    exit /b %ERRORLEVEL%
)

echo [2/3] Generation des types TypeScript...
cd frontend
npx openapi-typescript ..\schema.yaml -o src\types\api.d.ts

if %ERRORLEVEL% NEQ 0 (
    echo Erreur lors de la generation des types.
    cd ..
    exit /b %ERRORLEVEL%
)

echo [3/3] Nettoyage...
cd ..
echo SUCCESS: Frontend synchronise avec le Backend !

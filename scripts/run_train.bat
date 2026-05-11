@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Verification de l'environnement...
if exist ".venv\Scripts\activate.bat" (
    echo Activation de l'environnement virtuel...
    call ".venv\Scripts\activate.bat"
) else (
    echo Attention : Environnement virtuel non trouve !
)

echo Diagnostic CUDA...
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA disponible: {torch.cuda.is_available()}'); print(f'Nombre de GPU: {torch.cuda.device_count()}')"

echo.
echo Lancement de l'entrainement Otaku LLM...
python pipeline/mlops/train_expert_model.py
pause

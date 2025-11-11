@echo off
echo ================================================================================
echo TRAINING: 200 RUNS - PHASE 2 FULL FLOW (37 ASSERTIONS)
echo ================================================================================
echo.
echo Flow completo:
echo   - 10 steps (login, property+tabs, lead create/edit, navigation, delete)
echo   - 37 assertions, 28+ multi-selector fields
echo   - RL processing after EACH run
echo   - Patterns reloaded before each run
echo.
echo Estimated time: 8-12 hours
echo Checkpoints every 10 runs
echo.
echo Monitor progress: python analyze_training.py
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak > nul

cd /d "%~dp0"
python train_phase2_full_flow.py --runs 200 --headless > training_output.log 2>&1

echo.
echo ================================================================================
echo FINAL REPORT
echo ================================================================================
python generate_training_report.py

echo.
echo ================================================================================
echo TRAINING FINISHED
echo ================================================================================
pause


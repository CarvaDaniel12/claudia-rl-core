@echo off
echo ================================================================================
echo TEST: 5 RUNS TO VALIDATE BEFORE FULL TRAINING
echo ================================================================================
echo.
echo Testing multi-selector fallback + RL learning
echo This will take approximately 5-10 minutes
echo.
pause

cd /d "%~dp0"
python train_phase2_200runs.py --runs 5 --headless --process-every 1

echo.
echo ================================================================================
echo TEST COMPLETE
echo ================================================================================
echo Check results:
echo   - barril!!/ folder (5 run JSONs)
echo   - checkpoint_run5.json (stats)
echo.
echo If all 5 runs succeeded, you can run RUN_200_TRAINING.bat
pause


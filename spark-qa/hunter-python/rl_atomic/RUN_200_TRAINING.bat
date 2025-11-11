@echo off
echo ================================================================================
echo TRAINING: 200 RUNS PHASE 2 (HEADLESS)
echo ================================================================================
echo.
echo CONTINUOUS LEARNING MODE: RL processes after EACH run
echo This will run for approximately 5-7 hours (learning overhead)
echo Checkpoints saved every 50 runs
echo RL processing happens automatically
echo.
echo Press Ctrl+C to stop at any time (progress is saved)
echo.
pause

cd /d "%~dp0"
python train_phase2_200runs.py --runs 200 --headless --process-every 1

echo.
echo ================================================================================
echo TRAINING FINISHED
echo ================================================================================
echo Check barril!! folder for results
echo Check checkpoint_run*.json for progress
pause


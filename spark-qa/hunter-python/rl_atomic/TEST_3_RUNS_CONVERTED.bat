@echo off
echo ================================================================================
echo TEST: 3 RUNS - MULTI-SELECTOR CONVERSION VALIDATION
echo ================================================================================
echo.
echo Testing converted sections:
echo   - Property optional fields
echo   - Descriptions tab
echo   - Lead creation + guest info
echo.
echo Estimated time: 3-5 minutes
echo.
pause

cd /d "%~dp0"
python train_phase2_200runs.py --runs 3 --headless --process-every 1

echo.
echo ================================================================================
echo TEST RESULTS
echo ================================================================================
echo Check barril!!/ for 3 run JSONs
echo If all 3 succeeded, continue full conversion
pause


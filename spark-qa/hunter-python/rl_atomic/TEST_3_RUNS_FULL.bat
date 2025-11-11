@echo off
echo ================================================================================
echo TEST: 3 RUNS - FULL FLOW (37 ASSERTIONS, MULTI-SELECTOR)
echo ================================================================================
echo.
echo Testing complete flow_e2e_phase2.py:
echo   - 10 steps (login, property, descriptions, amenities, lead create/edit, nav, delete)
echo   - 37 assertions
echo   - Multi-selector fallback everywhere
echo   - RL learning after each run
echo.
echo Estimated time: 10-15 minutes
echo.
pause

cd /d "%~dp0"
python train_phase2_full_flow.py --runs 3 --headless

echo.
echo ================================================================================
echo TEST RESULTS
echo ================================================================================
echo Check:
echo   - barril!!/ (3 full run JSONs)
echo   - checkpoint_full_run3.json
echo.
echo If all 3 succeeded: ready for 200-run training
pause


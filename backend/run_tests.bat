@echo off
REM Test Scripts Runner for Windows
REM Run all StockIT test scripts

echo.
echo ================================================================================
echo   StockIT Test Suite
echo ================================================================================
echo.

:menu
echo Please select a test to run:
echo.
echo   1. Test Jira Connection (Quick - Raw API)
echo   2. Test Jira Service (Full - With Statistics)
echo   3. Test Authentication Flow
echo   4. Run All Tests
echo   5. Start Backend Server
echo   6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto test_jira_raw
if "%choice%"=="2" goto test_jira_full
if "%choice%"=="3" goto test_auth
if "%choice%"=="4" goto test_all
if "%choice%"=="5" goto start_server
if "%choice%"=="6" goto end

echo Invalid choice. Please try again.
goto menu

:test_jira_raw
echo.
echo ================================================================================
echo Running: Jira Raw API Test
echo ================================================================================
echo.
python test_jira_raw.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ Test failed! Check your Jira credentials in .env
    pause
) else (
    echo.
    echo ✅ Test completed! Check jira_raw_response.json for raw data
    pause
)
goto menu

:test_jira_full
echo.
echo ================================================================================
echo Running: Jira Service Test (Full)
echo ================================================================================
echo.
python test_jira_connection.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ Test failed! Check the output above for details
    pause
) else (
    echo.
    echo ✅ Test completed! Check jira_tickets_export.json for parsed data
    pause
)
goto menu

:test_auth
echo.
echo ================================================================================
echo Running: Authentication Flow Test
echo ================================================================================
echo.
echo Make sure the backend is running first!
echo   Start it with: uvicorn app.main:app --reload
echo.
pause
python test_auth_flow.py
pause
goto menu

:test_all
echo.
echo ================================================================================
echo Running All Tests
echo ================================================================================
echo.

echo [1/3] Testing Jira Raw API...
python test_jira_raw.py
set test1=%errorlevel%

echo.
echo [2/3] Testing Jira Service...
python test_jira_connection.py
set test2=%errorlevel%

echo.
echo [3/3] Testing Authentication (make sure backend is running)...
python test_auth_flow.py
set test3=%errorlevel%

echo.
echo ================================================================================
echo Test Results Summary
echo ================================================================================
echo.

if %test1% equ 0 (echo ✅ Jira Raw API Test: PASSED) else (echo ❌ Jira Raw API Test: FAILED)
if %test2% equ 0 (echo ✅ Jira Service Test: PASSED) else (echo ❌ Jira Service Test: FAILED)
if %test3% equ 0 (echo ✅ Auth Flow Test: PASSED) else (echo ❌ Auth Flow Test: FAILED)

echo.
pause
goto menu

:start_server
echo.
echo ================================================================================
echo Starting Backend Server
echo ================================================================================
echo.
echo Server will start with hot reload enabled
echo Press Ctrl+C to stop the server
echo.
pause
python -m uvicorn app.main:app --reload
goto menu

:end
echo.
echo Goodbye!
exit /b 0

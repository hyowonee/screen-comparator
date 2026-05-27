@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo 화면 코드 비교 분석 도구 - EXE 빌드
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않거나 PATH에 없습니다.
    pause
    exit /b 1
)

echo [1/4] 의존성 설치/확인...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
if errorlevel 1 (
    echo [오류] 의존성 설치에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo [2/4] 기존 빌드 산출물 정리...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [3/4] EXE 파일 빌드...
python -m PyInstaller screen-comparator.spec

if errorlevel 1 (
    echo [오류] 빌드에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo [4/4] 완성된 파일 확인...
if exist "dist\screen-comparator.exe" (
    echo ✓ dist\screen-comparator.exe 생성됨
    echo.
    echo [완료] dist 폴더의 screen-comparator.exe와 config.json을 같은 폴더에 두고 실행하세요.
) else (
    echo [오류] EXE 파일이 생성되지 않았습니다.
    pause
    exit /b 1
)

pause

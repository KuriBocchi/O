@echo off
chcp 65001 >nul
title O - Lore Asistani
cd /d "%~dp0"

echo.
echo   ========================================
echo           O  —  Lore Asistani
echo   ========================================
echo.

:: Python kontrolü (önce py, sonra python)
set PYTHON_CMD=
where py >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py
    echo [OK] py bulundu
) else (
    where python >nul 2>&1
    if %errorlevel%==0 (
        set PYTHON_CMD=python
        echo [OK] python bulundu
    )
)

if "%PYTHON_CMD%"=="" (
    echo.
    echo [HATA] Python bulunamadi!
    echo.
    echo Cozum:
    echo 1. baslat.bat'i kapattiktan sonra
    echo 2. Yeni Komut Istemi ac
    echo 3. Su komutu yaz:   py install 3.12
    echo 4. Kurulum bitince bilgisayari yeniden baslat
    echo 5. Sonra tekrar baslat.bat'i calistir
    echo.
    pause
    exit /b 1
)

echo Python komutu: %PYTHON_CMD%
echo.

:: Sanal ortam yoksa olustur
if not exist "venv" (
    echo Ilk kurulum basliyor... Bu 5-20 dakika surebilir.
    echo Lutfen pencereyi kapatma!
    echo.
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo.
        echo [HATA] Sanal ortam olusturulamadi.
        echo Yukaridaki hata mesajini oku.
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo Paketler yukleniyor...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [HATA] Paket yukleme basarisiz.
        echo Yukaridaki kirmizi hatalari oku ve bana gonder.
        pause
        exit /b 1
    )
    echo.
    echo Kurulum tamamlandi!
) else (
    call venv\Scripts\activate.bat
)

echo.
echo   O baslatiliyor...
echo   Tarayicida acilacak: http://localhost:8501
echo   Acilmazsa elle yaz:  http://localhost:8501
echo.
echo   Durdurmak icin bu pencerede Ctrl+C yap.
echo.

streamlit run app.py --server.headless true

echo.
echo Program kapandi.
pause

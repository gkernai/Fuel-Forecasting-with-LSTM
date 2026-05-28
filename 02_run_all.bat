@echo off
REM ============================================
REM  MASTER RUNNER - Tum adimlari sirayla calistirir
REM  sumo_project/ klasorunde calistir
REM ============================================

echo.
echo ========================================================
echo  TRAFIKTEKI GORUNMEZ GIDERLERIMIZ - SIMULASYON RUNNER
echo ========================================================
echo.

REM SUMO_HOME kontrolu
if "%SUMO_HOME%"=="" (
    echo HATA: SUMO_HOME ayarlanmamis!
    pause
    exit /b 1
)

echo [ADIM 1/4] Rota dosyalari olusturuluyor...
echo.
python scripts/generate_routes.py
if %errorlevel% neq 0 (
    echo HATA: Rota olusturma basarisiz!
    pause
    exit /b 1
)

echo.
echo [ADIM 2/4] TLS konfigurasyonlari olusturuluyor...
echo.
python scripts/generate_tls.py
if %errorlevel% neq 0 (
    echo HATA: TLS olusturma basarisiz!
    pause
    exit /b 1
)

echo.
echo [ADIM 3/4] SUMO konfigurasyonlari olusturuluyor...
echo.
python scripts/generate_configs.py
if %errorlevel% neq 0 (
    echo HATA: Config olusturma basarisiz!
    pause
    exit /b 1
)

echo.
echo ========================================================
echo  Opsiyonel: Simülasyonlari calistirmak icin asagidaki
echo  komutlardan birini kullan:
echo.
echo  TEK SENARYO (test icin):
echo    python scripts/collect_data.py --scenario scenario_1a --gui
echo.
echo  TUM SENARYOLAR (veri toplama):
echo    python scripts/collect_data.py --all
echo.
echo  SADECE OZET TABLO:
echo    python scripts/collect_data.py --summary-only
echo ========================================================
echo.

set /p CHOICE="Tum senaryolari simdi calistirmak ister misin? (e/h): "
if /i "%CHOICE%"=="e" (
    echo.
    echo [ADIM 4/4] Tum senaryolar calistiriliyor...
    echo Bu islem 20-40 dakika surebilir...
    echo.
    python scripts/collect_data.py --all
) else (
    echo.
    echo Tamam, senaryolari daha sonra kendin calistirabilirsin.
)

echo.
echo ========================================================
echo  TAMAMLANDI!
echo ========================================================
pause

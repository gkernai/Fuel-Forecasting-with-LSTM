@echo off
REM ============================================
REM  OSM -> SUMO Ağ Dönüştürme Scripti
REM  trafik_projesi/ klasöründe çalıştır
REM ============================================

echo.
echo ========================================
echo  SUMO Ag Donusturme Baslıyor...
echo ========================================
echo.

REM SUMO_HOME kontrolü
if "%SUMO_HOME%"=="" (
    echo HATA: SUMO_HOME ortam degiskeni ayarlanmamis!
    echo Lutfen su komutu calistir:
    echo   set SUMO_HOME=C:\Program Files ^(x86^)\Eclipse\Sumo
    pause
    exit /b 1
)

REM OSM dosyası kontrolü
if not exist "network\ankara_kizilay.osm" (
    echo HATA: network\ankara_kizilay.osm bulunamadi!
    echo Lutfen OSM dosyasini indirip network\ klasorune koy.
    echo Rehberdeki ADIM 2'yi takip et.
    pause
    exit /b 1
)

echo [1/3] netconvert calistiriliyor...
echo.

netconvert --osm-files network/ankara_kizilay.osm ^
           --type-files network/typemap.xml ^
           --output-file network/ankara.net.xml ^
           --geometry.remove ^
           --ramps.guess ^
           --junctions.join ^
           --tls.guess-signals true ^
           --tls.join true ^
           --tls.default-type actuated ^
           --edges.join true ^
           --osm.all-attributes true ^
           --keep-edges.by-type "highway.motorway,highway.motorway_link,highway.trunk,highway.trunk_link,highway.primary,highway.primary_link,highway.secondary,highway.secondary_link,highway.tertiary,highway.tertiary_link,highway.residential,highway.unclassified,highway.living_street" ^
           --remove-edges.isolated true

if %errorlevel% neq 0 (
    echo.
    echo HATA: netconvert basarisiz oldu!
    pause
    exit /b 1
)

echo.
echo [2/3] Ag dosyasi olusturuldu: network\ankara.net.xml
echo.

REM Dosya boyutunu göster
for %%A in (network\ankara.net.xml) do echo Dosya boyutu: %%~zA bytes

echo.
echo [3/3] Ag istatistikleri cikartiliyor...
echo.

python scripts/network_stats.py

echo.
echo ========================================
echo  TAMAMLANDI!
echo  sumo-gui -n network/ankara.net.xml
echo  komutuyla agi goruntuleyebilirsin.
echo ========================================
echo.
pause

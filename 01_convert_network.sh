#!/bin/bash

echo ""
echo "========================================"
echo "  SUMO Ağ Dönüştürme Başlıyor..."
echo "========================================"
echo ""

# SUMO_HOME kontrolü
if [ -z "$SUMO_HOME" ]; then
    echo "HATA: SUMO_HOME ortam değişkeni ayarlanmamış!"
    echo "  export SUMO_HOME=/usr/share/sumo"
    exit 1
fi

# OSM dosyası kontrolü
if [ ! -f "network/ankara_kizilay.osm" ]; then
    echo "HATA: network/ankara_kizilay.osm bulunamadı!"
    echo "Rehberdeki ADIM 2'yi takip et."
    exit 1
fi

echo "[1/3] netconvert çalıştırılıyor..."

netconvert --osm-files network/ankara_kizilay.osm \
           --type-files network/typemap.xml \
           --output-file network/ankara.net.xml \
           --geometry.remove \
           --ramps.guess \
           --junctions.join \
           --tls.guess-signals true \
           --tls.join true \
           --tls.default-type actuated \
           --edges.join true \
           --osm.all-attributes true \
           --keep-edges.by-type "highway.motorway,highway.motorway_link,highway.trunk,highway.trunk_link,highway.primary,highway.primary_link,highway.secondary,highway.secondary_link,highway.tertiary,highway.tertiary_link,highway.residential,highway.unclassified,highway.living_street" \
           --remove-edges.isolated true

if [ $? -ne 0 ]; then
    echo "HATA: netconvert başarısız oldu!"
    exit 1
fi

echo ""
echo "[2/3] Ağ dosyası oluşturuldu: network/ankara.net.xml"
ls -lh network/ankara.net.xml
echo ""
echo "[3/3] Ağ istatistikleri çıkartılıyor..."
echo ""

python3 scripts/network_stats.py

echo ""
echo "========================================"
echo "  TAMAMLANDI!"
echo "  sumo-gui -n network/ankara.net.xml"
echo "========================================"

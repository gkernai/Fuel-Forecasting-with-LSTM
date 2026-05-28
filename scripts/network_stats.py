
import os
import sys
import xml.etree.ElementTree as ET


if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    print("UYARI: SUMO_HOME ortam değişkeni ayarlanmamış!")
    print("Lütfen SUMO_HOME'u ayarla:")
    print("  Windows: set SUMO_HOME=C:\\Program Files (x86)\\Eclipse\\Sumo")
    print("  Linux:   export SUMO_HOME=/usr/share/sumo")

import sumolib

def analyze_network(net_file="network/ankara.net.xml"):
    
    if not os.path.exists(net_file):
        print(f"HATA: {net_file} bulunamadı!")
        print("Önce netconvert komutunu çalıştırdığından emin ol.")
        return
    
    print("=" * 60)
    print("  AĞ İSTATİSTİKLERİ")
    print("=" * 60)
    
    net = sumolib.net.readNet(net_file)
    

    edges = net.getEdges()
    nodes = net.getNodes()
    tls_list = net.getTrafficLights()
    
    print(f"\n{'Toplam Edge (yol segmenti) sayısı:':<45} {len(edges)}")
    print(f"{'Toplam Node (kavşak) sayısı:':<45} {len(nodes)}")
    print(f"{'Trafik Işığı (TLS) sayısı:':<45} {len(tls_list)}")
    

    total_lanes = sum(len(e.getLanes()) for e in edges)
    print(f"{'Toplam şerit sayısı:':<45} {total_lanes}")
    

    total_length = sum(e.getLength() for e in edges)
    print(f"{'Toplam yol uzunluğu:':<45} {total_length:.0f} m ({total_length/1000:.2f} km)")
    

    print(f"\n{'--- Hız Limitleri ---'}")
    speed_counts = {}
    for e in edges:
        speed_kmh = round(e.getSpeed() * 3.6)  # m/s → km/h
        speed_counts[speed_kmh] = speed_counts.get(speed_kmh, 0) + 1
    
    for speed in sorted(speed_counts.keys()):
        count = speed_counts[speed]
        print(f"  {speed:>3} km/h: {count} edge")
    

    print(f"\n{'--- Şerit Sayısı Dağılımı ---'}")
    lane_counts = {}
    for e in edges:
        n_lanes = len(e.getLanes())
        lane_counts[n_lanes] = lane_counts.get(n_lanes, 0) + 1
    
    for lanes in sorted(lane_counts.keys()):
        count = lane_counts[lanes]
        print(f"  {lanes} şerit: {count} edge")
    
    print(f"\n{'--- Kavşak Tipi Dağılımı ---'}")
    junction_types = {}
    for n in nodes:
        jtype = n.getType()
        junction_types[jtype] = junction_types.get(jtype, 0) + 1
    
    for jtype, count in sorted(junction_types.items(), key=lambda x: -x[1]):
        print(f"  {jtype:<30} {count}")
    

    if tls_list:
        print(f"\n{'--- Trafik Işıkları (İlk 10) ---'}")
        for i, tls in enumerate(tls_list[:10]):
            tls_id = tls.getID()
            programs = tls.getPrograms()
            for prog_id, prog in programs.items():
                phases = prog.getPhases()
                print(f"  TLS '{tls_id}' → {len(phases)} faz, program: {prog_id}")
    

    print(f"\n{'--- Bağlantı Kontrolü ---'}")
    isolated = []
    for e in edges:
        incoming = e.getIncoming()
        outgoing = e.getOutgoing()
        if len(incoming) == 0 and len(outgoing) == 0:
            isolated.append(e.getID())
    
    if isolated:
        print(f"  UYARI: {len(isolated)} izole edge bulundu!")
        for eid in isolated[:5]:
            print(f"    - {eid}")
        if len(isolated) > 5:
            print(f"    ... ve {len(isolated)-5} tane daha")
    else:
        print("  Tüm edge'ler bağlı — sorun yok!")
    

    print(f"\n{'--- Örnek Edge ID'leri (ilk 15) ---'}")
    for e in edges[:15]:
        speed_kmh = round(e.getSpeed() * 3.6)
        n_lanes = len(e.getLanes())
        length = e.getLength()
        print(f"  {e.getID():<40} {n_lanes} şerit, {speed_kmh} km/h, {length:.0f}m")
    
    print("\n" + "=" * 60)
    print("  Ağ analizi tamamlandı!")
    print("  Sonraki adım: Talep dosyalarını oluşturmak.")
    print("=" * 60)


if __name__ == "__main__":
    analyze_network()

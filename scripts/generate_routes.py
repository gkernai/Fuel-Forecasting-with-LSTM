import os
import sys
import subprocess

# SUMO_HOME kontrolu
SUMO_HOME = os.environ.get("SUMO_HOME", "")
if not SUMO_HOME:
    print("HATA: SUMO_HOME ayarlanmamis!")
    sys.exit(1)

RANDOM_TRIPS = os.path.join(SUMO_HOME, "tools", "randomTrips.py")
NET_FILE = "network/ankara.net.xml"
DEMAND_DIR = "demand"

os.makedirs(DEMAND_DIR, exist_ok=True)


def run_cmd(cmd, description):
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    print(f"  Komut: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  HATA: {result.stderr[:300]}")
        return False
    else:
        print(f"  BASARILI!")
        return True


def generate_scenario(name, description, period, begin, end,
                      extra_args=None):
    trip_file = os.path.join(DEMAND_DIR, f"{name}.trips.xml")
    route_file = os.path.join(DEMAND_DIR, f"{name}.rou.xml")

    # randomTrips.py ile trip olustur
    cmd = [
        sys.executable, RANDOM_TRIPS,
        "-n", NET_FILE,
        "-o", trip_file,
        "-r", route_file,
        "-b", str(begin),
        "-e", str(end),
        "-p", str(period),
        "--fringe-factor", "5",        # kenar yollardan giris/cikis onceligi
        "--validate",                   # gecersiz rotalari ele
        "--random",                     # rastgele seed
        "--trip-attributes", 'type="passenger"',
    ]

    if extra_args:
        cmd.extend(extra_args)

    return run_cmd(cmd, f"Senaryo {name}: {description}")


def main():
    print("\n" + "#"*60)
    print("  ROTA URETIMI BASLADI")
    print("  9 alt senaryo icin talep dosyalari olusturuluyor...")
    print("#"*60)

    scenarios = []
    scenarios.append(
        generate_scenario(
            name="scenario_1a",
            description="Sabah pik (1200 arac/saat, sabit TLS)",
            period=3.0,
            begin=0,
            end=3600,
        )
    )

    # 1b: Normal akis - 600 arac/saat -> period = 6
    scenarios.append(
        generate_scenario(
            name="scenario_1b",
            description="Normal akis (600 arac/saat, sabit TLS)",
            period=6.0,
            begin=0,
            end=3600,
        )
    )

    # 1c: Aksam pik - 1200 arac/saat -> period = 3
    scenarios.append(
        generate_scenario(
            name="scenario_1c",
            description="Aksam pik (1200 arac/saat, sabit TLS)",
            period=3.0,
            begin=0,
            end=3600,
        )
    )
    scenarios.append(
        generate_scenario(
            name="scenario_2a_burst",
            description="Mac cikisi - patlama fazı (ilk 10 dk, 3000 arac/saat)",
            period=1.2,
            begin=0,
            end=600,
        )
    )

    scenarios.append(
        generate_scenario(
            name="scenario_2a_tail",
            description="Mac cikisi - kuyruk fazı (kalan 50 dk, 1200 arac/saat)",
            period=3.0,
            begin=600,
            end=3600,
        )
    )

    scenarios.append(
        generate_scenario(
            name="scenario_2b",
            description="Surekli yogun (1800 arac/saat)",
            period=2.0,
            begin=0,
            end=3600,
        )
    )

    scenarios.append(
        generate_scenario(
            name="scenario_2c",
            description="Kaza senaryosu (1200 arac/saat, serit kapanmasi TraCI ile)",
            period=3.0,
            begin=0,
            end=3600,
        )
    )
    import shutil
    src = os.path.join(DEMAND_DIR, "scenario_1a.rou.xml")
    if os.path.exists(src):
        for suffix in ["3a", "3b", "3c"]:
            dst = os.path.join(DEMAND_DIR, f"scenario_{suffix}.rou.xml")
            shutil.copy2(src, dst)
            print(f"\n  Senaryo {suffix}: scenario_1a.rou.xml kopyalandi (ayni talep)")
            scenarios.append(True)
    else:
        print("\n  UYARI: scenario_1a.rou.xml bulunamadi, 3a/3b/3c olusturulamadi!")
    merge_2a_files()


    success = sum(1 for s in scenarios if s)
    print(f"\n{'#'*60}")
    print(f"  TAMAMLANDI: {success}/{len(scenarios)} senaryo basarili")
    print(f"  Dosyalar: {DEMAND_DIR}/ klasorunde")
    print(f"{'#'*60}\n")


    print("  Olusturulan dosyalar:")
    for f in sorted(os.listdir(DEMAND_DIR)):
        if f.endswith(".rou.xml"):
            fpath = os.path.join(DEMAND_DIR, f)
            size = os.path.getsize(fpath) / 1024
            print(f"    {f:<40} {size:.0f} KB")


def merge_2a_files():
    """Senaryo 2a: burst + tail dosyalarini tek bir rou.xml'e birlestirir."""
    burst_file = os.path.join(DEMAND_DIR, "scenario_2a_burst.rou.xml")
    tail_file = os.path.join(DEMAND_DIR, "scenario_2a_tail.rou.xml")
    output_file = os.path.join(DEMAND_DIR, "scenario_2a.rou.xml")

    if not os.path.exists(burst_file) or not os.path.exists(tail_file):
        print("\n  UYARI: 2a burst/tail dosyalari bulunamadi, birlestirme atlandi.")
        return

    import xml.etree.ElementTree as ET

    tree1 = ET.parse(burst_file)
    tree2 = ET.parse(tail_file)

    root = ET.Element("routes")


    vtype = ET.SubElement(root, "vType")
    vtype.set("id", "passenger")
    vtype.set("vClass", "passenger")


    for vehicle in tree1.getroot().iter("vehicle"):
        root.append(vehicle)

    counter = 10000
    for vehicle in tree2.getroot().iter("vehicle"):
        vehicle.set("id", f"tail_{counter}")
        counter += 1
        root.append(vehicle)

    tree_out = ET.ElementTree(root)
    ET.indent(tree_out, space="    ")
    tree_out.write(output_file, encoding="UTF-8", xml_declaration=True)
    print(f"\n  Senaryo 2a: burst + tail birlestirildi -> {output_file}")


if __name__ == "__main__":
    main()

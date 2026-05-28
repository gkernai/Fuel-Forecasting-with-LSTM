
import os
import xml.etree.ElementTree as ET

NET_FILE = "../network/ankara.net.xml"
CONFIG_DIR = "config"
os.makedirs(CONFIG_DIR, exist_ok=True)

SCENARIOS = {
    # === SENARYO 1: STANDART ===
    "scenario_1a": {
        "route": "../demand/scenario_1a.rou.xml",
        "tls": "tls_fixed.add.xml",
        "desc": "Sabah pik - sabit TLS"
    },
    "scenario_1b": {
        "route": "../demand/scenario_1b.rou.xml",
        "tls": "tls_fixed.add.xml",
        "desc": "Normal akis - sabit TLS"
    },
    "scenario_1c": {
        "route": "../demand/scenario_1c.rou.xml",
        "tls": "tls_fixed.add.xml",
        "desc": "Aksam pik - sabit TLS"
    },
    # === SENARYO 2: KAOS ===
    "scenario_2a": {
        "route": "../demand/scenario_2a.rou.xml",
        "tls": "tls_fixed.add.xml",
        "desc": "Mac cikisi - sabit TLS"
    },
    "scenario_2b": {
        "route": "../demand/scenario_2b.rou.xml",
        "tls": "tls_fixed.add.xml",
        "desc": "Surekli yogun - sabit TLS"
    },
    "scenario_2c": {
        "route": "../demand/scenario_2c.rou.xml",
        "tls": "tls_fixed.add.xml",
        "desc": "Kaza senaryosu - sabit TLS"
    },
    # === SENARYO 3: OPTIMIZE ===
    "scenario_3a": {
        "route": "../demand/scenario_3a.rou.xml",
        "tls": "tls_greenwave.add.xml",
        "desc": "Greenwave - yesil dalga"
    },
    "scenario_3b": {
        "route": "../demand/scenario_3b.rou.xml",
        "tls": "tls_actuated.add.xml",
        "desc": "Adaptif TLS"
    },
    "scenario_3c": {
        "route": "../demand/scenario_3c.rou.xml",
        "tls": "tls_actuated.add.xml",
        "desc": "Tam optimizasyon"
    },
}


def create_sumocfg(name, route_file, tls_file, output_dir):
    """Tek bir senaryo icin .sumocfg dosyasi olusturur."""
    
    root = ET.Element("configuration")

    # Input
    inp = ET.SubElement(root, "input")
    net = ET.SubElement(inp, "net-file")
    net.set("value", NET_FILE)
    route = ET.SubElement(inp, "route-files")
    route.set("value", route_file)
    add = ET.SubElement(inp, "additional-files")
    add.set("value", tls_file)

    # Time
    time = ET.SubElement(root, "time")
    begin = ET.SubElement(time, "begin")
    begin.set("value", "0")
    end = ET.SubElement(time, "end")
    end.set("value", "3600")
    step = ET.SubElement(time, "step-length")
    step.set("value", "1.0")

    # Processing
    proc = ET.SubElement(root, "processing")
    tele = ET.SubElement(proc, "time-to-teleport")
    tele.set("value", "120")  

    # Output (istatistik)
    output = ET.SubElement(root, "output")
    stat = ET.SubElement(output, "statistic-output")
    stat.set("value", f"../output/{name}_stats.xml")

    filepath = os.path.join(output_dir, f"{name}.sumocfg")
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(filepath, encoding="UTF-8", xml_declaration=True)
    return filepath


def main():
    print("\n" + "#"*60)
    print("  SUMO KONFIGÜRASYON DOSYALARI OLUSTURULUYOR")
    print("#"*60)

    for name, info in SCENARIOS.items():
        filepath = create_sumocfg(
            name=name,
            route_file=info["route"],
            tls_file=info["tls"],
            output_dir=CONFIG_DIR
        )
        print(f"  {name:<20} -> {filepath:<45} ({info['desc']})")

    print(f"\n  Toplam {len(SCENARIOS)} config dosyasi olusturuldu.")
    print(f"  Konum: {CONFIG_DIR}/")
    print(f"\n{'#'*60}\n")


if __name__ == "__main__":
    main()

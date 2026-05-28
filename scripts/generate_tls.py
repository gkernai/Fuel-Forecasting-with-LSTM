import os
import sys
import xml.etree.ElementTree as ET

SUMO_HOME = os.environ.get("SUMO_HOME", "")
if SUMO_HOME:
    sys.path.append(os.path.join(SUMO_HOME, "tools"))

import sumolib

NET_FILE = "network/ankara.net.xml"
CONFIG_DIR = "config"
os.makedirs(CONFIG_DIR, exist_ok=True)


def get_tls_info(net_file):

    net = sumolib.net.readNet(net_file)
    tls_list = net.getTrafficLights()
    
    print(f"\n  Toplam TLS sayisi: {len(tls_list)}")
    print(f"  TLS ID'leri:")
    for tls in tls_list:
        programs = tls.getPrograms()
        for pid, prog in programs.items():
            phases = prog.getPhases()
            print(f"    {tls.getID():<30} {len(phases)} faz, program: {pid}")
    
    return tls_list


def generate_fixed_time_tls(net_file, output_file, cycle_time=90):

    net = sumolib.net.readNet(net_file)
    tls_list = net.getTrafficLights()

    root = ET.Element("additional")

    for tls in tls_list:
        tls_id = tls.getID()
        programs = tls.getPrograms()

        for pid, prog in programs.items():
            phases = prog.getPhases()
            num_phases = len(phases)

          
            tl_logic = ET.SubElement(root, "tlLogic")
            tl_logic.set("id", tls_id)
            tl_logic.set("type", "static")
            tl_logic.set("programID", "fixed")
            tl_logic.set("offset", "0")

            if num_phases > 0:
               
                green_phases = [p for p in phases if 'y' not in p.state.lower()]
                yellow_phases = [p for p in phases if 'y' in p.state.lower()]
                
                num_green = max(len(green_phases), 1)
                yellow_time = 4
                total_yellow = len(yellow_phases) * yellow_time
                green_time = max(int((cycle_time - total_yellow) / num_green), 15)

                for phase in phases:
                    ph = ET.SubElement(tl_logic, "phase")
                    ph.set("state", phase.state)
                    if 'y' in phase.state.lower():
                        ph.set("duration", str(yellow_time))
                    else:
                        ph.set("duration", str(green_time))

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)
    print(f"\n  Fixed-time TLS -> {output_file}")
    print(f"  Cycle time: ~{cycle_time}s, {len(tls_list)} TLS guncellendi")


def generate_greenwave_tls(net_file, output_file, green_time=45,
                           offset_step=8):
    """
    Yesil dalga (greenwave) TLS programi olusturur.
    Ataturk Bulvari boyunca sirayla offset vererek yesil dalga olusturur.
    Senaryo 3a icin kullanilir.
    """
    net = sumolib.net.readNet(net_file)
    tls_list = net.getTrafficLights()

    tls_positions = []
    for tls in tls_list:
        tls_id = tls.getID()
    
        connections = tls.getConnections()
        if connections:
         
            first_conn = connections[0]
            from_lane = first_conn[0]  
            edge = from_lane.getEdge()
            shape = edge.getShape()
            if shape:
                mid_y = sum(p[1] for p in shape) / len(shape)
                tls_positions.append((tls_id, mid_y))


    tls_positions.sort(key=lambda x: x[1])

    root = ET.Element("additional")

    for idx, (tls_id, _) in enumerate(tls_positions):
        tls = net.getTLSSecurityID(tls_id) if hasattr(net, 'getTLSSecurityID') else None
        
        for t in tls_list:
            if t.getID() == tls_id:
                tls_obj = t
                break
        
        programs = tls_obj.getPrograms()
        for pid, prog in programs.items():
            phases = prog.getPhases()

            tl_logic = ET.SubElement(root, "tlLogic")
            tl_logic.set("id", tls_id)
            tl_logic.set("type", "static")
            tl_logic.set("programID", "greenwave")
            tl_logic.set("offset", str(idx * offset_step))

            for phase in phases:
                ph = ET.SubElement(tl_logic, "phase")
                ph.set("state", phase.state)
                if 'y' in phase.state.lower():
                    ph.set("duration", "4")
                else:
                    ph.set("duration", str(green_time))

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)
    print(f"\n  Greenwave TLS -> {output_file}")
    print(f"  {len(tls_positions)} TLS, offset_step={offset_step}s")


def generate_actuated_tls(net_file, output_file, min_dur=15,
                          max_dur=55):

    net = sumolib.net.readNet(net_file)
    tls_list = net.getTrafficLights()

    root = ET.Element("additional")

    for tls in tls_list:
        tls_id = tls.getID()
        programs = tls.getPrograms()

        for pid, prog in programs.items():
            phases = prog.getPhases()

            tl_logic = ET.SubElement(root, "tlLogic")
            tl_logic.set("id", tls_id)
            tl_logic.set("type", "actuated")
            tl_logic.set("programID", "actuated")
            tl_logic.set("offset", "0")

            # Actuated parametreleri
            param_gap = ET.SubElement(tl_logic, "param")
            param_gap.set("key", "max-gap")
            param_gap.set("value", "3.0")

            param_pass = ET.SubElement(tl_logic, "param")
            param_pass.set("key", "passage-time")
            param_pass.set("value", "2.0")

            param_det = ET.SubElement(tl_logic, "param")
            param_det.set("key", "detector-gap")
            param_det.set("value", "1.0")

            for phase in phases:
                ph = ET.SubElement(tl_logic, "phase")
                ph.set("state", phase.state)
                if 'y' in phase.state.lower():
                    ph.set("duration", "4")
                    ph.set("minDur", "4")
                    ph.set("maxDur", "4")
                else:
                    ph.set("duration", str(min_dur))
                    ph.set("minDur", str(min_dur))
                    ph.set("maxDur", str(max_dur))

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)
    print(f"\n  Actuated TLS -> {output_file}")
    print(f"  minDur={min_dur}s, maxDur={max_dur}s, {len(tls_list)} TLS")


def main():
    print("\n" + "#"*60)
    print("  TLS KONFIGURASYONLARI OLUSTURULUYOR")
    print("#"*60)


    get_tls_info(NET_FILE)

    generate_fixed_time_tls(
        NET_FILE,
        os.path.join(CONFIG_DIR, "tls_fixed.add.xml"),
        cycle_time=90
    )

    generate_greenwave_tls(
        NET_FILE,
        os.path.join(CONFIG_DIR, "tls_greenwave.add.xml"),
        green_time=45,
        offset_step=8
    )

    generate_actuated_tls(
        NET_FILE,
        os.path.join(CONFIG_DIR, "tls_actuated.add.xml"),
        min_dur=15,
        max_dur=55
    )

    print(f"\n{'#'*60}")
    print("  TLS konfigurasyonlari tamamlandi!")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()

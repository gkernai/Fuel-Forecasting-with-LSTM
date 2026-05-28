import glob
import xml.etree.ElementTree as ET

for f in glob.glob("demand/*.rou.xml"):
    print(f"Fixing: {f}")
    tree = ET.parse(f)
    root = tree.getroot()
    
    # Eski vType varsa sil
    for vt in root.findall("vType"):
        root.remove(vt)
    
    # Yeni vType ekle (en basa)
    vtype = ET.Element("vType")
    vtype.set("id", "passenger")
    vtype.set("vClass", "passenger")
    vtype.set("emissionClass", "HBEFA3/PC_G_EU4")
    root.insert(0, vtype)
    
    ET.indent(tree, space="    ")
    tree.write(f, encoding="UTF-8", xml_declaration=True)
    print(f"  OK!")

print("\nTamamlandi!")
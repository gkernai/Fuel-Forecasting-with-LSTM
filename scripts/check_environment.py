

import os
import sys
import shutil
import subprocess

def check_item(name, result, detail=""):
    status = "✓" if result else "✗"
    color_status = f"[{status}]"
    print(f"  {color_status} {name}")
    if detail and not result:
        print(f"      → {detail}")
    return result

def main():
    print("=" * 50)
    print("  SUMO ORTAM KONTROLÜ")
    print("=" * 50)
    print()
    
    all_ok = True
    
    # 1. SUMO_HOME
    sumo_home = os.environ.get('SUMO_HOME', '')
    ok = check_item(
        "SUMO_HOME ortam değişkeni",
        bool(sumo_home),
        "SUMO_HOME ayarlanmamış! Kurulum rehberine bak."
    )
    all_ok = all_ok and ok
    if sumo_home:
        print(f"      → {sumo_home}")
    
    # 2. sumo binary
    sumo_bin = shutil.which('sumo')
    ok = check_item(
        "sumo komutu PATH'te",
        sumo_bin is not None,
        "sumo PATH'te bulunamadı. SUMO bin klasörünü PATH'e ekle."
    )
    all_ok = all_ok and ok
    
    # 3. netconvert
    nc_bin = shutil.which('netconvert')
    ok = check_item(
        "netconvert komutu",
        nc_bin is not None,
        "netconvert bulunamadı."
    )
    all_ok = all_ok and ok
    
    # 4. sumo-gui
    gui_bin = shutil.which('sumo-gui')
    ok = check_item(
        "sumo-gui komutu",
        gui_bin is not None,
        "sumo-gui bulunamadı (opsiyonel ama önerilir)."
    )
    
    # 5. netedit
    ne_bin = shutil.which('netedit')
    ok = check_item(
        "netedit komutu",
        ne_bin is not None,
        "netedit bulunamadı (opsiyonel)."
    )

    try:
        if sumo_home:
            sys.path.append(os.path.join(sumo_home, 'tools'))
        import traci
        ok = check_item("Python traci modülü", True)
    except ImportError:
        ok = check_item(
            "Python traci modülü",
            False,
            "traci import edilemedi. SUMO_HOME/tools PATH'e ekli mi?"
        )
        all_ok = all_ok and ok
    
    # 7. Python sumolib
    try:
        import sumolib
        ok = check_item("Python sumolib modülü", True)
    except ImportError:
        ok = check_item(
            "Python sumolib modülü",
            False,
            "sumolib import edilemedi."
        )
        all_ok = all_ok and ok
    

    py_ver = sys.version_info
    ok = check_item(
        f"Python sürümü ({py_ver.major}.{py_ver.minor}.{py_ver.micro})",
        py_ver.major == 3 and py_ver.minor >= 8,
        "Python 3.8+ önerilir."
    )
    

    print()
    print("  Ek Python paketleri (pip install gerekebilir):")
    for pkg in ['pandas', 'numpy', 'matplotlib', 'torch', 'seaborn']:
        try:
            __import__(pkg)
            check_item(f"  {pkg}", True)
        except ImportError:
            check_item(
                f"  {pkg}",
                False,
                f"pip install {pkg}"
            )

    print()
    print("  Proje klasör yapısı:")
    for folder in ['network', 'demand', 'config', 'output', 'scripts', 'plots', 'model']:
        exists = os.path.isdir(folder)
        check_item(f"  {folder}/", exists, f"mkdir {folder}")
        if not exists:
            all_ok = False
    
    # Sonuç
    print()
    print("=" * 50)
    if all_ok:
        print("  Her şey hazır! Devam edebilirsin.")
    else:
        print("  Bazı sorunlar var. Yukarıdaki ✗ işaretlerini düzelt.")
    print("=" * 50)


if __name__ == "__main__":
    main()

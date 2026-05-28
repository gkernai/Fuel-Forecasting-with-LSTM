
import os
import sys
import csv
import time
import argparse
from datetime import datetime


SUMO_HOME = os.environ.get("SUMO_HOME", "")
if SUMO_HOME:
    sys.path.append(os.path.join(SUMO_HOME, "tools"))

import traci


NET_FILE = "network/ankara.net.xml"
CONFIG_DIR = "config"
OUTPUT_DIR = "output"
DURATION = 3600  # 1 saat

os.makedirs(OUTPUT_DIR, exist_ok=True)


ALL_SCENARIOS = [
    "scenario_1a", "scenario_1b", "scenario_1c",
    "scenario_2a", "scenario_2b", "scenario_2c",
    "scenario_3a", "scenario_3b", "scenario_3c",
]


def run_simulation(scenario_name, use_gui=False):
    """
    Tek bir senaryo icin SUMO simulasyonunu calistirir ve
    adim adim veri toplar.
    """
    config_file = os.path.join(CONFIG_DIR, f"{scenario_name}.sumocfg")

    if not os.path.exists(config_file):
        print(f"  HATA: {config_file} bulunamadi! Atlaniyor.")
        return None

    # SUMO komutunu hazirla
    sumo_binary = "sumo-gui" if use_gui else "sumo"
    sumo_cmd = [sumo_binary, "-c", config_file, "--start", "--quit-on-end"]

    print(f"\n{'='*60}")
    print(f"  SENARYO: {scenario_name}")
    print(f"  Config:  {config_file}")
    print(f"  Binary:  {sumo_binary}")
    print(f"  Baslangic: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

  
    traci.start(sumo_cmd)


    csv_file = os.path.join(OUTPUT_DIR, f"{scenario_name}_data.csv")
    fieldnames = [
        "step",              # simulasyon adimi (s)
        "vehicle_count",     # aktif arac sayisi
        "mean_speed",        # ortalama hiz (m/s)
        "total_fuel_ml_s",   # toplam yakit tuketimi (ml/s)
        "total_co2_mg_s",    # toplam CO2 emisyonu (mg/s)
        "total_waiting_s",   # toplam bekleme suresi (s)
        "halting_count",     # duran arac sayisi
        "departed_count",    # o adimda aga giren arac
        "arrived_count",     # o adimda hedefe ulasan arac
        "mean_fuel_per_veh", # arac basi ort. yakit (ml/s)
        "mean_co2_per_veh",  # arac basi ort. CO2 (mg/s)
    ]

    data_rows = []
    start_time = time.time()

    step = 0
    while step < DURATION:
        traci.simulationStep()

        # Aktif araclari al
        vehicles = traci.vehicle.getIDList()
        veh_count = len(vehicles)

        if veh_count > 0:
            speeds = []
            fuels = []
            co2s = []
            waitings = []
            halting = 0

            for v in vehicles:
                spd = traci.vehicle.getSpeed(v)
                speeds.append(spd)
                fuels.append(traci.vehicle.getFuelConsumption(v))
                co2s.append(traci.vehicle.getCO2Emission(v))
                waitings.append(traci.vehicle.getWaitingTime(v))
                if spd < 0.1:
                    halting += 1

            total_fuel = sum(fuels)
            total_co2 = sum(co2s)
            total_waiting = sum(waitings)
            mean_speed = sum(speeds) / veh_count
            mean_fuel = total_fuel / veh_count
            mean_co2 = total_co2 / veh_count
        else:
            total_fuel = 0
            total_co2 = 0
            total_waiting = 0
            mean_speed = 0
            halting = 0
            mean_fuel = 0
            mean_co2 = 0
        departed = traci.simulation.getDepartedNumber()
        arrived = traci.simulation.getArrivedNumber()

        row = {
            "step": step,
            "vehicle_count": veh_count,
            "mean_speed": round(mean_speed, 4),
            "total_fuel_ml_s": round(total_fuel, 4),
            "total_co2_mg_s": round(total_co2, 4),
            "total_waiting_s": round(total_waiting, 4),
            "halting_count": halting,
            "departed_count": departed,
            "arrived_count": arrived,
            "mean_fuel_per_veh": round(mean_fuel, 4),
            "mean_co2_per_veh": round(mean_co2, 4),
        }
        data_rows.append(row)

    
        if scenario_name == "scenario_2c" and step == 900:
            simulate_accident(vehicles)
        if step % 600 == 0:
            elapsed = time.time() - start_time
            print(f"  [{step:>4}/{DURATION}] "
                  f"Arac: {veh_count:>4} | "
                  f"Hiz: {mean_speed:>5.1f} m/s | "
                  f"Yakit: {total_fuel:>8.1f} ml/s | "
                  f"CO2: {total_co2:>10.1f} mg/s | "
                  f"Duran: {halting:>4} | "
                  f"Sure: {elapsed:>5.1f}s")

        step += 1


    traci.close()

    # CSV'ye yaz
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_rows)

    elapsed_total = time.time() - start_time
    print(f"\n  Tamamlandi: {elapsed_total:.1f} saniye")
    print(f"  CSV kaydedildi: {csv_file}")
    print(f"  Toplam veri noktasi: {len(data_rows)}")

    # Ozet istatistikler
    if data_rows:
        avg_veh = sum(r["vehicle_count"] for r in data_rows) / len(data_rows)
        total_fuel_all = sum(r["total_fuel_ml_s"] for r in data_rows)
        total_co2_all = sum(r["total_co2_mg_s"] for r in data_rows)
        avg_wait = sum(r["total_waiting_s"] for r in data_rows) / len(data_rows)

        print(f"\n  --- OZET ---")
        print(f"  Ort. aktif arac:     {avg_veh:.0f}")
        print(f"  Toplam yakit:        {total_fuel_all:.0f} ml "
              f"({total_fuel_all/1000:.2f} litre)")
        print(f"  Toplam CO2:          {total_co2_all:.0f} mg "
              f"({total_co2_all/1e6:.2f} kg)")
        print(f"  Ort. bekleme:        {avg_wait:.1f} s/adim")

    return csv_file


def simulate_accident(vehicles):
    """
    Kaza senaryosu: Agdaki bir araci durdurur ve serit kapatir.
    15. dakikada cagrilir.
    """
    print(f"\n  !!! KAZA SIMULASYONU BASLADI (adim 900) !!!")
    
    if len(vehicles) > 0:
       
        accident_vehicle = vehicles[len(vehicles) // 2]
        try:
            traci.vehicle.setSpeed(accident_vehicle, 0)
            traci.vehicle.setColor(accident_vehicle, (255, 0, 0, 255))
            
           
            edge_id = traci.vehicle.getRoadID(accident_vehicle)
            if edge_id and not edge_id.startswith(":"):
                traci.edge.setMaxSpeed(edge_id, 2.0)  
                print(f"  Kaza araci: {accident_vehicle}")
                print(f"  Etkilenen yol: {edge_id} (hiz limiti 2 m/s)")
        except Exception as e:
            print(f"  Kaza simulasyonu hatasi: {e}")


def generate_summary_csv(output_dir):
    """Tum senaryolarin ozet istatistiklerini tek bir CSV'de topla."""
    
    summary_file = os.path.join(output_dir, "summary_all_scenarios.csv")
    summary_fields = [
        "scenario", "avg_vehicle_count", "avg_mean_speed",
        "total_fuel_litre", "total_co2_kg",
        "avg_waiting_s", "avg_halting_count",
        "max_vehicle_count", "min_mean_speed"
    ]
    
    summary_rows = []
    
    for scenario in ALL_SCENARIOS:
        csv_file = os.path.join(output_dir, f"{scenario}_data.csv")
        if not os.path.exists(csv_file):
            continue
        
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            continue
        
        n = len(rows)
        avg_veh = sum(float(r["vehicle_count"]) for r in rows) / n
        avg_spd = sum(float(r["mean_speed"]) for r in rows) / n
        total_fuel = sum(float(r["total_fuel_ml_s"]) for r in rows) / 1000
        total_co2 = sum(float(r["total_co2_mg_s"]) for r in rows) / 1e6
        avg_wait = sum(float(r["total_waiting_s"]) for r in rows) / n
        avg_halt = sum(float(r["halting_count"]) for r in rows) / n
        max_veh = max(float(r["vehicle_count"]) for r in rows)
        min_spd = min(float(r["mean_speed"]) for r in rows)
        
        summary_rows.append({
            "scenario": scenario,
            "avg_vehicle_count": round(avg_veh, 1),
            "avg_mean_speed": round(avg_spd, 2),
            "total_fuel_litre": round(total_fuel, 2),
            "total_co2_kg": round(total_co2, 3),
            "avg_waiting_s": round(avg_wait, 1),
            "avg_halting_count": round(avg_halt, 1),
            "max_vehicle_count": int(max_veh),
            "min_mean_speed": round(min_spd, 2),
        })
    
    if summary_rows:
        with open(summary_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=summary_fields)
            writer.writeheader()
            writer.writerows(summary_rows)
        print(f"\n  Ozet dosya: {summary_file}")
        
        # Ekrana yazdir
        print(f"\n  {'Senaryo':<16} {'Ort.Arac':>8} {'Ort.Hiz':>8} "
              f"{'Yakit(L)':>9} {'CO2(kg)':>8} {'Bekleme':>8}")
        print(f"  {'-'*60}")
        for r in summary_rows:
            print(f"  {r['scenario']:<16} {r['avg_vehicle_count']:>8.0f} "
                  f"{r['avg_mean_speed']:>7.2f} "
                  f"{r['total_fuel_litre']:>9.2f} "
                  f"{r['total_co2_kg']:>8.3f} "
                  f"{r['avg_waiting_s']:>8.1f}")


def main():
    parser = argparse.ArgumentParser(
        description="SUMO TraCI Veri Toplama"
    )
    parser.add_argument(
        "--scenario", type=str, default=None,
        help="Tek senaryo calistir (ornek: scenario_1a)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Tum senaryolari sirayla calistir"
    )
    parser.add_argument(
        "--gui", action="store_true",
        help="SUMO GUI ile calistir (gorsel)"
    )
    parser.add_argument(
        "--summary-only", action="store_true",
        help="Sadece ozet tablosu olustur (simulasyon calismaz)"
    )
    args = parser.parse_args()

    if args.summary_only:
        generate_summary_csv(OUTPUT_DIR)
        return

    if args.scenario:
        # Tek senaryo
        run_simulation(args.scenario, use_gui=args.gui)
    elif args.all:
        # Tum senaryolar
        print("\n" + "#"*60)
        print("  TUM SENARYOLAR CALISTIRILIYOR")
        print(f"  Toplam: {len(ALL_SCENARIOS)} senaryo x {DURATION}s")
        print("#"*60)

        results = []
        total_start = time.time()

        for scenario in ALL_SCENARIOS:
            csv_path = run_simulation(scenario, use_gui=args.gui)
            results.append((scenario, csv_path))

        total_elapsed = time.time() - total_start
        print(f"\n{'#'*60}")
        print(f"  TUMU TAMAMLANDI: {total_elapsed:.0f} saniye "
              f"({total_elapsed/60:.1f} dakika)")
        print(f"{'#'*60}")

        # Ozet tablosu olustur
        generate_summary_csv(OUTPUT_DIR)
    else:
        print("Kullanim:")
        print("  python scripts/collect_data.py --scenario scenario_1a")
        print("  python scripts/collect_data.py --scenario scenario_1a --gui")
        print("  python scripts/collect_data.py --all")
        print("  python scripts/collect_data.py --summary-only")


if __name__ == "__main__":
    main()

"""
SUNUM DEMO SCRIPTI
==================
Egitilmis LSTM modelini yukler ve canli tahmin yapar.
Sunumda calistirip hocaya gostereceksin.

Kullanim:
    cd sumo_project
    python scripts/demo.py

3 demo modu var:
  1. Canli tahmin - CSV'den veri okuyup gercek vs tahmin gosterir
  2. Manuel girdi - sen deger giriyorsun, model tahmin yapiyor
  3. Senaryo karsilastirma - farkli senaryolarin tahminlerini yan yana gosterir
"""

import os
import sys
import csv
import time
import numpy as np

try:
    import torch
    import torch.nn as nn
except ImportError:
    print("HATA: PyTorch bulunamadi! pip install torch")
    sys.exit(1)

# ============================================================
# MODEL TANIMI (egitimde kullanilan ayni mimari)
# ============================================================
class TrafficLSTM(nn.Module):
    def __init__(self, input_size=3, hidden_size=64,
                 num_layers=2, output_size=2):
        super(TrafficLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                            batch_first=True, dropout=0.2)
        self.fc1 = nn.Linear(hidden_size, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0),
                          self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0),
                          self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.relu(self.fc1(out[:, -1, :]))
        return self.fc2(out)


# ============================================================
# YARDIMCI FONKSIYONLAR
# ============================================================
MODEL_PATH = "model/traffic_lstm.pth"
OUTPUT_DIR = "output"
SEQ_LEN = 60
INPUT_COLS = ["vehicle_count", "mean_speed", "halting_count"]
OUTPUT_COLS = ["total_fuel_ml_s", "total_co2_mg_s"]


def load_model():
    """Egitilmis modeli yukle."""
    if not os.path.exists(MODEL_PATH):
        print(f"HATA: {MODEL_PATH} bulunamadi!")
        print("Once python scripts/train_lstm.py calistir.")
        sys.exit(1)

    checkpoint = torch.load(MODEL_PATH, map_location="cpu",
                            weights_only=False)
    model = TrafficLSTM(
        input_size=checkpoint.get("input_size", 3),
        hidden_size=checkpoint.get("hidden_size", 64),
        num_layers=checkpoint.get("num_layers", 2),
        output_size=checkpoint.get("output_size", 2),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    print(f"  Model yuklendi: {MODEL_PATH}")
    print(f"  Egitim MSE:  {checkpoint.get('train_loss', '?'):.6f}")
    print(f"  Test MSE:    {checkpoint.get('test_loss', '?'):.6f}")
    return model


def load_scenario_data(scenario):
    """CSV verisini yukle."""
    path = os.path.join(OUTPUT_DIR, f"{scenario}_data.csv")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def compute_norm_params():
    """Tum egitim verisi uzerinden min-max parametrelerini hesapla."""
    all_data = []
    for sc in ["scenario_1a", "scenario_1b", "scenario_1c",
               "scenario_2a", "scenario_2b", "scenario_2c"]:
        data = load_scenario_data(sc)
        if data:
            for row in data:
                vals = [float(row[c]) for c in INPUT_COLS + OUTPUT_COLS]
                all_data.append(vals)
    arr = np.array(all_data, dtype=np.float32)
    d_min = arr.min(axis=0)
    d_max = arr.max(axis=0)
    d_range = d_max - d_min
    d_range[d_range == 0] = 1
    return d_min, d_max, d_range


def predict(model, sequence, d_min, d_range):
    """
    60 adimlik veri dizisi alip tahmin yapar.
    sequence: list of [vehicle_count, mean_speed, halting_count]
    """
    n_in = len(INPUT_COLS)
    seq = np.array(sequence, dtype=np.float32)
    seq_norm = (seq - d_min[:n_in]) / d_range[:n_in]

    x = torch.FloatTensor(seq_norm).unsqueeze(0)  # (1, 60, 3)
    with torch.no_grad():
        pred_norm = model(x).numpy()[0]

    # Denormalize
    pred = pred_norm * d_range[n_in:] + d_min[n_in:]
    return pred  # [fuel_ml_s, co2_mg_s]


# ============================================================
# DEMO 1: CSV'den canli tahmin
# ============================================================
def demo_live_prediction(model, d_min, d_range):
    """CSV verisinden adim adim tahmin yapar, gercekle karsilastirir."""
    print("\n" + "=" * 65)
    print("  DEMO 1: Canli Tahmin (Senaryo 1a)")
    print("  Model her adimda son 60 saniyelik veriye bakip tahmin yapiyor")
    print("=" * 65)

    data = load_scenario_data("scenario_1a")
    if not data:
        print("  HATA: scenario_1a_data.csv bulunamadi!")
        return

    n_in = len(INPUT_COLS)

    print(f"\n  {'Adim':>6}  {'Arac':>5}  {'Hiz':>6}  "
          f"{'Gercek Yakit':>13}  {'Tahmin Yakit':>13}  "
          f"{'Gercek CO2':>11}  {'Tahmin CO2':>11}  {'Fark':>6}")
    print(f"  {'-' * 75}")

    buffer = []
    for i, row in enumerate(data):
        vals = [float(row[c]) for c in INPUT_COLS]
        buffer.append(vals)

        if len(buffer) < SEQ_LEN + 1:
            continue
        if len(buffer) > SEQ_LEN + 1:
            buffer.pop(0)

        # Son 60 adimi al
        seq = buffer[:SEQ_LEN]
        pred = predict(model, seq, d_min, d_range)

        actual_fuel = float(row["total_fuel_ml_s"])
        actual_co2 = float(row["total_co2_mg_s"])
        fuel_err = abs(pred[0] - actual_fuel) / max(actual_fuel, 1) * 100

        # Her 300 adimda (5 dk) goster
        if i % 300 == 0 and i > SEQ_LEN:
            print(f"  {i:>6}  {int(vals[0]):>5}  {vals[1]:>6.1f}  "
                  f"{actual_fuel:>13,.0f}  {pred[0]:>13,.0f}  "
                  f"{actual_co2:>11,.0f}  {pred[1]:>11,.0f}  "
                  f"{fuel_err:>5.1f}%")
            time.sleep(0.3)  # sunumda dramatik etki icin

    print(f"\n  Tahmin tamamlandi!")


# ============================================================
# DEMO 2: Manuel girdi
# ============================================================
def demo_manual_input(model, d_min, d_range):
    """Kullanicinin girdigi degerlere gore tahmin yapar."""
    print("\n" + "=" * 65)
    print("  DEMO 2: Manuel Tahmin")
    print("  Trafik degerlerini gir, model yakit ve CO2 tahmin etsin")
    print("=" * 65)

    presets = [
        ("Normal trafik (az arac, yuksek hiz)",
         50, 11.0, 1),
        ("Yogun trafik (cok arac, dusuk hiz)",
         120, 6.0, 15),
        ("Kaza sonrasi (orta arac, cok dusuk hiz, cok duran)",
         90, 3.0, 40),
    ]

    print(f"\n  Hazir senaryolar:")
    for idx, (name, v, s, h) in enumerate(presets, 1):
        print(f"    {idx}. {name}")
        print(f"       Arac: {v}, Hiz: {s} m/s, Duran: {h}")
    print(f"    4. Kendi degerlerimi girmek istiyorum")

    try:
        choice = input("\n  Secimin (1-4): ").strip()
    except EOFError:
        choice = "0"

    if choice in ["1", "2", "3"]:
        _, veh, spd, halt = presets[int(choice) - 1]
    elif choice == "4":
        try:
            veh = int(input("  Arac sayisi (ornek 80): ") or "80")
            spd = float(input("  Ortalama hiz m/s (ornek 10): ") or "10")
            halt = int(input("  Duran arac sayisi (ornek 3): ") or "3")
        except (ValueError, EOFError):
            veh, spd, halt = 80, 10.0, 3
    else:
        veh, spd, halt = 80, 10.0, 3

    # 60 adimlik sabit dizi olustur (ayni degerleri tekrarla)
    seq = [[veh, spd, halt]] * SEQ_LEN
    pred = predict(model, seq, d_min, d_range)

    print(f"\n  {'=' * 45}")
    print(f"  GIRDI:")
    print(f"    Arac sayisi:       {veh}")
    print(f"    Ortalama hiz:      {spd} m/s")
    print(f"    Duran arac:        {halt}")
    print(f"\n  MODEL TAHMINI:")
    print(f"    Yakit tuketimi:    {pred[0]:,.0f} ml/s")
    print(f"    CO2 emisyonu:      {pred[1]:,.0f} mg/s")
    print(f"\n  1 SAATLIK PROJEKSIYON:")
    print(f"    Toplam yakit:      {pred[0] * 3600 / 1000:,.1f} litre")
    print(f"    Toplam CO2:        {pred[1] * 3600 / 1e6:,.2f} kg")
    print(f"    Yakit maliyeti:    {pred[0] * 3600 / 1000 * 52:,.0f} TL")
    print(f"  {'=' * 45}")


# ============================================================
# DEMO 3: Senaryo karsilastirma
# ============================================================
def demo_scenario_comparison(model, d_min, d_range):
    """Farkli senaryolarin son 60 adimini modele verip karsilastirir."""
    print("\n" + "=" * 65)
    print("  DEMO 3: Senaryo Karsilastirma")
    print("  Her senaryodan 60 adimlik dilim alip tahmin yapiyoruz")
    print("=" * 65)

    scenarios = {
        "1a: Sabah pik":    "scenario_1a",
        "1b: Normal":       "scenario_1b",
        "2a: Mac cikisi":   "scenario_2a",
        "2b: Surekli yogun":"scenario_2b",
        "2c: Kaza":         "scenario_2c",
    }

    print(f"\n  {'Senaryo':<22} {'Tahmin Yakit':>13} {'Tahmin CO2':>12} "
          f"{'Gercek Yakit':>13} {'Gercek CO2':>12}")
    print(f"  {'-' * 75}")

    for label, sc_name in scenarios.items():
        data = load_scenario_data(sc_name)
        if not data or len(data) < SEQ_LEN + 100:
            continue

        # Ortalardan 60 adimlik dilim al
        mid = len(data) // 2
        seq = []
        for i in range(mid, mid + SEQ_LEN):
            row = data[i]
            seq.append([float(row[c]) for c in INPUT_COLS])

        pred = predict(model, seq, d_min, d_range)
        actual_row = data[mid + SEQ_LEN]
        actual_fuel = float(actual_row["total_fuel_ml_s"])
        actual_co2 = float(actual_row["total_co2_mg_s"])

        print(f"  {label:<22} {pred[0]:>13,.0f} {pred[1]:>12,.0f} "
              f"{actual_fuel:>13,.0f} {actual_co2:>12,.0f}")
        time.sleep(0.2)

    print()


# ============================================================
# ANA MENU
# ============================================================
def main():
    print("\n" + "#" * 65)
    print("  TRAFIKTEKI GORUNMEZ GIDERLER - LSTM DEMO")
    print("#" * 65)

    model = load_model()
    d_min, d_max, d_range = compute_norm_params()

    while True:
        print(f"\n  Demo secenekleri:")
        print(f"    1. Canli tahmin (CSV'den adim adim)")
        print(f"    2. Manuel girdi (sen deger gir, model tahmin etsin)")
        print(f"    3. Senaryo karsilastirma")
        print(f"    q. Cikis")

        try:
            choice = input("\n  Secimin: ").strip().lower()
        except EOFError:
            break

        if choice == "1":
            demo_live_prediction(model, d_min, d_range)
        elif choice == "2":
            demo_manual_input(model, d_min, d_range)
        elif choice == "3":
            demo_scenario_comparison(model, d_min, d_range)
        elif choice == "q":
            print("\n  Gule gule!")
            break
        else:
            print("  1, 2, 3 veya q gir.")


if __name__ == "__main__":
    main()

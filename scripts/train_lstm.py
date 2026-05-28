import os
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# PyTorch
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("PyTorch bulunamadi")

OUTPUT_DIR = "output"
MODEL_DIR = "model"
PLOTS_DIR = "plots"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

# Hyperparametreler
SEQ_LEN = 60        
HIDDEN_SIZE = 64
NUM_LAYERS = 2
EPOCHS = 50
BATCH_SIZE = 32
LR = 0.001
TRAIN_RATIO = 0.8

# Girdi ve cikti degiskenleri
INPUT_COLS = ['vehicle_count', 'mean_speed', 'halting_count']
OUTPUT_COLS = ['total_fuel_ml_s', 'total_co2_mg_s']


class TrafficLSTM(nn.Module):
    "
    
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(TrafficLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True, dropout=0.2
        )
        self.fc1 = nn.Linear(hidden_size, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, output_size)
    
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        out = out[:, -1, :] 
        out = self.relu(self.fc1(out))
        out = self.fc2(out)
        return out


def load_and_prepare_data():
    #eğitimde senaryo 1a ve 2a kullanıldı.
    train_scenarios = [
        'scenario_1a', 'scenario_1b', 'scenario_1c',
        'scenario_2a', 'scenario_2b', 'scenario_2c',
    ]
    
    all_data = []
    for scenario in train_scenarios:
        filepath = os.path.join(OUTPUT_DIR, f"{scenario}_data.csv")
        if not os.path.exists(filepath):
            print(f"  UYARI: {filepath} bulunamadi, atlaniyor.")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                values = [float(row[col]) for col in INPUT_COLS + OUTPUT_COLS]
                all_data.append(values)
    
    if not all_data:
        print("HATA: Veri bulunamadi!")
        return None, None, None, None, None
    
    data = np.array(all_data, dtype=np.float32)
    print(f"  Toplam veri noktasi: {len(data)}")
    print(f"  Girdi boyutu: {len(INPUT_COLS)}, Cikti boyutu: {len(OUTPUT_COLS)}")
    
    # Normalizasyon (min-max)
    data_min = data.min(axis=0)
    data_max = data.max(axis=0)
    data_range = data_max - data_min
    data_range[data_range == 0] = 1  # sifira bolme engeli
    data_norm = (data - data_min) / data_range
    
    # Sequence olustur
    X, Y = [], []
    n_input = len(INPUT_COLS)
    
    for i in range(len(data_norm) - SEQ_LEN):
        X.append(data_norm[i:i+SEQ_LEN, :n_input])
        Y.append(data_norm[i+SEQ_LEN, n_input:])
    
    X = np.array(X)
    Y = np.array(Y)
    
    print(f"  Sequence sayisi: {len(X)}")
    print(f"  X shape: {X.shape}, Y shape: {Y.shape}")
    
    # Train/test bolumu
    split_idx = int(len(X) * TRAIN_RATIO)
    X_train, X_test = X[:split_idx], X[split_idx:]
    Y_train, Y_test = Y[:split_idx], Y[split_idx:]
    
    print(f"  Egitim: {len(X_train)}, Test: {len(X_test)}")
    
    # Denormalizasyon icin parametreleri kaydet
    norm_params = {
        'data_min': data_min,
        'data_max': data_max,
        'data_range': data_range,
    }
    
    return X_train, Y_train, X_test, Y_test, norm_params


def train_model(X_train, Y_train, X_test, Y_test):
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"  Device: {device}")
    
    # Tensor'lere cevir
    X_train_t = torch.FloatTensor(X_train).to(device)
    Y_train_t = torch.FloatTensor(Y_train).to(device)
    X_test_t = torch.FloatTensor(X_test).to(device)
    Y_test_t = torch.FloatTensor(Y_test).to(device)
    
    # DataLoader
    train_dataset = TensorDataset(X_train_t, Y_train_t)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    # Model
    model = TrafficLSTM(
        input_size=len(INPUT_COLS),
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS,
        output_size=len(OUTPUT_COLS)
    ).to(device)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    
    print(f"\n  Model parametreleri: {sum(p.numel() for p in model.parameters()):,}")
    print(f"  Epochs: {EPOCHS}, Batch: {BATCH_SIZE}, LR: {LR}")
    print(f"  Seq len: {SEQ_LEN}, Hidden: {HIDDEN_SIZE}, Layers: {NUM_LAYERS}")
    
    # Egitim dongusu
    train_losses = []
    test_losses = []
    
    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0
        n_batches = 0
        
        for batch_X, batch_Y in train_loader:
            optimizer.zero_grad()
            output = model(batch_X)
            loss = criterion(output, batch_Y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            n_batches += 1
        
        avg_train_loss = epoch_loss / n_batches
        train_losses.append(avg_train_loss)
        
        # Test loss
        model.eval()
        with torch.no_grad():
            test_pred = model(X_test_t)
            test_loss = criterion(test_pred, Y_test_t).item()
            test_losses.append(test_loss)
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"  Epoch [{epoch+1:>3}/{EPOCHS}]  "
                  f"Train Loss: {avg_train_loss:.6f}  "
                  f"Test Loss: {test_loss:.6f}")
    
    # Modeli kaydet
    model_path = os.path.join(MODEL_DIR, "traffic_lstm.pth")
    torch.save({
        'model_state_dict': model.state_dict(),
        'input_size': len(INPUT_COLS),
        'hidden_size': HIDDEN_SIZE,
        'num_layers': NUM_LAYERS,
        'output_size': len(OUTPUT_COLS),
        'seq_len': SEQ_LEN,
        'train_loss': train_losses[-1],
        'test_loss': test_losses[-1],
    }, model_path)
    print(f"\n  Model kaydedildi: {model_path}")
    
    # Tahminleri al
    model.eval()
    with torch.no_grad():
        predictions = model(X_test_t).cpu().numpy()
        actuals = Y_test_t.cpu().numpy()
    
    return train_losses, test_losses, predictions, actuals


def plot_loss_curve(train_losses, test_losses):
    """Loss egrisini ciz."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    epochs = range(1, len(train_losses) + 1)
    ax.plot(epochs, train_losses, 'b-', label='Egitim Loss', linewidth=1.5)
    ax.plot(epochs, test_losses, 'r-', label='Test Loss', linewidth=1.5)
    
    ax.set_xlabel('Epoch', fontsize=12)
    ax.set_ylabel('MSE Loss', fontsize=12)
    ax.set_title('LSTM Model Egitim Egrisi', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)
    
    # Son degerler
    ax.annotate(f'Son: {train_losses[-1]:.6f}', 
                xy=(len(train_losses), train_losses[-1]),
                fontsize=9, color='blue')
    ax.annotate(f'Son: {test_losses[-1]:.6f}',
                xy=(len(test_losses), test_losses[-1]),
                fontsize=9, color='red')
    
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig7_loss_curve.png'))
    plt.close()
    print("  fig7_loss_curve.png")


def plot_predictions(predictions, actuals, norm_params):
    """Gercek vs tahmin grafigi."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    n_input = len(INPUT_COLS)
    
    for i, (col_name, unit) in enumerate(zip(OUTPUT_COLS, ['ml/s', 'mg/s'])):
        ax = axes[i]
        
        # Denormalize işlemi...
        pred_denorm = predictions[:, i] * norm_params['data_range'][n_input + i] + norm_params['data_min'][n_input + i]
        actual_denorm = actuals[:, i] * norm_params['data_range'][n_input + i] + norm_params['data_min'][n_input + i]
        
        # Ilk 500 nokta
        n_show = min(500, len(pred_denorm))
        x = range(n_show)
        
        ax.plot(x, actual_denorm[:n_show], 'b-', alpha=0.7, label='Gercek', linewidth=0.8)
        ax.plot(x, pred_denorm[:n_show], 'r-', alpha=0.7, label='Tahmin', linewidth=0.8)
        
        # Hata metrikleri
        mse = np.mean((pred_denorm - actual_denorm) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(pred_denorm - actual_denorm))
        
        label_clean = 'Yakit Tuketimi' if 'fuel' in col_name else 'CO2 Emisyonu'
        ax.set_title(f'{label_clean}\nRMSE: {rmse:.2f}, MAE: {mae:.2f}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Zaman Adimi', fontsize=10)
        ax.set_ylabel(f'{label_clean} ({unit})', fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3)
    
    fig.suptitle('LSTM Model: Gercek vs Tahmin (Test Seti)', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig8_predictions.png'), bbox_inches='tight')
    plt.close()
    print("  fig8_predictions.png")
    
    #metrik kntorlü
    n_input = len(INPUT_COLS)
    for i, col in enumerate(OUTPUT_COLS):
        pred_d = predictions[:, i] * norm_params['data_range'][n_input+i] + norm_params['data_min'][n_input+i]
        act_d = actuals[:, i] * norm_params['data_range'][n_input+i] + norm_params['data_min'][n_input+i]
        
        mse = np.mean((pred_d - act_d) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(pred_d - act_d))
        r2 = 1 - np.sum((pred_d - act_d)**2) / np.sum((act_d - np.mean(act_d))**2)
        
        print(f"\n  {col}:")
        print(f"    MSE:  {mse:.4f}")
        print(f"    RMSE: {rmse:.4f}")
        print(f"    MAE:  {mae:.4f}")
        print(f"    R2:   {r2:.4f}")


def main():
    if not HAS_TORCH:
        print("PyTorch bulunamadı")
        return
    

    print("Eğtiim başlıyor...")
    
    
    # Veri yuükleme
    print("  Veri yukleniyor...")
    X_train, Y_train, X_test, Y_test, norm_params = load_and_prepare_data()
    
    if X_train is None:
        return
    
    # Egitim
    print("\n  Egitim basladi...")
    train_losses, test_losses, predictions, actuals = train_model(
        X_train, Y_train, X_test, Y_test
    )
    
    # Eğtim Grafikleri
    print("\n  Grafikler olusturuluyor...")
    plot_loss_curve(train_losses, test_losses)
    plot_predictions(predictions, actuals, norm_params)
    
    print(f"\n{'#'*60}")
    print("  LSTM egitimi tamamlandi!")
    print(f"  Model: {MODEL_DIR}/traffic_lstm.pth")
    print(f"  Grafikler: {PLOTS_DIR}/")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()

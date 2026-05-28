import os
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

OUTPUT_DIR = "output"
PLOTS_DIR = "plots"
os.makedirs(PLOTS_DIR, exist_ok=True)


plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['figure.figsize'] = (12, 6)

# Renk paleti
COLORS = {
    'scenario_1a': '#3B82F6',  
    'scenario_1b': '#93C5FD',  
    'scenario_1c': '#1D4ED8', 
    'scenario_2a': '#EF4444',  
    'scenario_2b': '#DC2626', 
    'scenario_2c': '#F97316',  
    'scenario_3a': '#22C55E', 
    'scenario_3b': '#16A34A',  
    'scenario_3c': '#15803D', 
}

LABELS = {
    'scenario_1a': '1a: Sabah Pik',
    'scenario_1b': '1b: Normal',
    'scenario_1c': '1c: Aksam Pik',
    'scenario_2a': '2a: Mac Cikisi',
    'scenario_2b': '2b: Surekli Yogun',
    'scenario_2c': '2c: Kaza',
    'scenario_3a': '3a: Greenwave',
    'scenario_3b': '3b: Adaptif TLS',
    'scenario_3c': '3c: Tam Optimizasyon',
}

GROUP_COLORS = {
    'Standart': '#3B82F6',
    'Kaos': '#EF4444',
    'Optimize': '#22C55E',
}


def load_scenario_data(scenario_name):
    
    filepath = os.path.join(OUTPUT_DIR, f"{scenario_name}_data.csv")
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({k: float(v) for k, v in row.items()})
    return rows


def load_summary():
   
    filepath = os.path.join(OUTPUT_DIR, "summary_all_scenarios.csv")
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def plot_1_fuel_comparison_bar():
    
    summary = load_summary()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    names = [s['scenario'] for s in summary]
    fuels = [float(s['total_fuel_litre']) for s in summary]
    colors = [COLORS.get(n, '#888') for n in names]
    labels = [LABELS.get(n, n) for n in names]
    
    bars = ax.bar(labels, fuels, color=colors, edgecolor='white', linewidth=0.5)
    
  
    for bar, val in zip(bars, fuels):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5000,
                f'{val/1000:.0f}K L', ha='center', va='bottom', fontsize=9)
    
    ax.set_ylabel('Toplam Yakit Tuketimi (Litre)', fontsize=12)
    ax.set_title('Senaryo Bazinda Toplam Yakit Tuketimi (1 Saat)', fontsize=14, fontweight='bold')
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig1_fuel_comparison.png'))
    plt.close()
    print("  [1/6] fig1_fuel_comparison.png")


def plot_2_co2_comparison_bar():
    summary = load_summary()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    names = [s['scenario'] for s in summary]
    co2s = [float(s['total_co2_kg']) for s in summary]
    colors = [COLORS.get(n, '#888') for n in names]
    labels = [LABELS.get(n, n) for n in names]
    
    bars = ax.bar(labels, co2s, color=colors, edgecolor='white', linewidth=0.5)
    
    for bar, val in zip(bars, co2s):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                f'{val:.0f} kg', ha='center', va='bottom', fontsize=9)
    
    ax.set_ylabel('Toplam CO2 Emisyonu (kg)', fontsize=12)
    ax.set_title('Senaryo Bazinda Toplam CO2 Emisyonu (1 Saat)', fontsize=14, fontweight='bold')
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig2_co2_comparison.png'))
    plt.close()
    print("  [2/6] fig2_co2_comparison.png")


def plot_3_group_comparison():
    summary = load_summary()
    
    groups = {
        'Standart\n(Senaryo 1)': ['scenario_1a', 'scenario_1c'],  
        'Kaos\n(Senaryo 2)': ['scenario_2a', 'scenario_2b'],      
        'Optimize\n(Senaryo 3)': ['scenario_3a'],
    }
    
    metrics = {
        'Yakit (L)': 'total_fuel_litre',
        'CO2 (kg)': 'total_co2_kg',
        'Bekleme (s)': 'avg_waiting_s',
    }
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for ax_idx, (metric_label, metric_key) in enumerate(metrics.items()):
        ax = axes[ax_idx]
        group_names = list(groups.keys())
        group_avgs = []
        
        for gname, scenarios in groups.items():
            vals = []
            for s in summary:
                if s['scenario'] in scenarios:
                    vals.append(float(s[metric_key]))
            group_avgs.append(np.mean(vals) if vals else 0)
        
        colors_list = ['#3B82F6', '#EF4444', '#22C55E']
        bars = ax.bar(group_names, group_avgs, color=colors_list, 
                      edgecolor='white', linewidth=0.5, width=0.6)
        
        for bar, val in zip(bars, group_avgs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.02,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_title(metric_label, fontsize=13, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    fig.suptitle('Senaryo Gruplari Arasi Karsilastirma', fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig3_group_comparison.png'), bbox_inches='tight')
    plt.close()
    print("  [3/6] fig3_group_comparison.png")


def plot_4_time_series(scenarios_to_plot=None):
    if scenarios_to_plot is None:
        scenarios_to_plot = ['scenario_1a', 'scenario_2a', 'scenario_2b']
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    for scenario in scenarios_to_plot:
        data = load_scenario_data(scenario)
        if not data:
            continue
        
        steps = [d['step'] for d in data]
        fuels = [d['total_fuel_ml_s'] for d in data]
        co2s = [d['total_co2_mg_s'] for d in data]
        color = COLORS.get(scenario, '#888')
        label = LABELS.get(scenario, scenario)
        
        # Smoothing (hareketli ortalama, 60 adim = 1 dk)
        window = 60
        if len(fuels) > window:
            fuels_smooth = np.convolve(fuels, np.ones(window)/window, mode='valid')
            co2_smooth = np.convolve(co2s, np.ones(window)/window, mode='valid')
            steps_smooth = steps[:len(fuels_smooth)]
        else:
            fuels_smooth = fuels
            co2_smooth = co2s
            steps_smooth = steps
        
        # Dakikaya cevir
        minutes = [s/60 for s in steps_smooth]
        
        axes[0].plot(minutes, fuels_smooth, color=color, label=label, linewidth=1.2, alpha=0.85)
        axes[1].plot(minutes, co2_smooth, color=color, label=label, linewidth=1.2, alpha=0.85)
    
    axes[0].set_ylabel('Yakit Tuketimi (ml/s)', fontsize=11)
    axes[0].set_title('Zaman Serisi: Yakit Tuketimi ve CO2 Emisyonu', fontsize=14, fontweight='bold')
    axes[0].legend(loc='upper right', fontsize=9)
    axes[0].grid(alpha=0.3)
    
    axes[1].set_ylabel('CO2 Emisyonu (mg/s)', fontsize=11)
    axes[1].set_xlabel('Zaman (dakika)', fontsize=11)
    axes[1].legend(loc='upper right', fontsize=9)
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig4_time_series.png'))
    plt.close()
    print("  [4/6] fig4_time_series.png")


def plot_5_waiting_time():
    scenarios = ['scenario_1a', 'scenario_2a', 'scenario_2c']
    
    fig, ax = plt.subplots(figsize=(14, 5))
    
    for scenario in scenarios:
        data = load_scenario_data(scenario)
        if not data:
            continue
        
        steps = [d['step']/60 for d in data]  # dakika
        waiting = [d['total_waiting_s'] for d in data]
        color = COLORS.get(scenario, '#888')
        label = LABELS.get(scenario, scenario)
        
        # Smoothing
        window = 30
        if len(waiting) > window:
            smooth = np.convolve(waiting, np.ones(window)/window, mode='valid')
            steps_s = steps[:len(smooth)]
        else:
            smooth = waiting
            steps_s = steps
        
        ax.plot(steps_s, smooth, color=color, label=label, linewidth=1.5)
    
    # Kaza noktasini isaretle
    ax.axvline(x=15, color='red', linestyle='--', alpha=0.5, linewidth=1)
    ax.annotate('Kaza (15. dk)', xy=(15, ax.get_ylim()[1]*0.9),
                fontsize=10, color='red', ha='center')
    
    ax.set_xlabel('Zaman (dakika)', fontsize=11)
    ax.set_ylabel('Toplam Bekleme Suresi (s)', fontsize=11)
    ax.set_title('Bekleme Suresi: Normal vs Kaos vs Kaza', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig5_waiting_time.png'))
    plt.close()
    print("  [5/6] fig5_waiting_time.png")


def plot_6_cost_analysis():
    summary = load_summary()
    BENZIN_TL_PER_LITRE = 52.0 
    SAAT_MALIYET_TL = 120.0     
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    names = []
    fuel_costs = []
    time_costs = []
    
    for s in summary:
        name = LABELS.get(s['scenario'], s['scenario'])
        names.append(name)
        
        fuel_litre = float(s['total_fuel_litre'])
        fuel_cost = fuel_litre * BENZIN_TL_PER_LITRE
        fuel_costs.append(fuel_cost)
        
        avg_wait = float(s['avg_waiting_s'])
        avg_veh = float(s['avg_vehicle_count'])
        # Toplam bekleme suresi x arac sayisi -> saat -> TL
        total_wait_hours = (avg_wait * avg_veh * 3600) / 3600 / 3600
        time_cost = total_wait_hours * SAAT_MALIYET_TL
        time_costs.append(time_cost)
    
    x = np.arange(len(names))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, [f/1e6 for f in fuel_costs], width,
                   label='Yakit Maliyeti', color='#F97316', edgecolor='white')
    bars2 = ax.bar(x + width/2, [t/1e3 for t in time_costs], width,
                   label='Zaman Maliyeti (x1000)', color='#8B5CF6', edgecolor='white')
    
    ax.set_ylabel('Maliyet (Milyon TL / Bin TL)', fontsize=11)
    ax.set_title(f'Gorunmez Giderler: Maliyet Analizi\n(Benzin: {BENZIN_TL_PER_LITRE} TL/L, Firsat Maliyeti: {SAAT_MALIYET_TL} TL/saat)',
                 fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=30, ha='right', fontsize=9)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig6_cost_analysis.png'))
    plt.close()
    print("  [6/6] fig6_cost_analysis.png")


def print_cost_table():
    summary = load_summary()
    
    BENZIN_TL = 52.0
    
    print(f"\n{'='*70}")
    print(f"  MALIYET ANALIZI (Benzin: {BENZIN_TL} TL/L)")
    print(f"{'='*70}")
    print(f"  {'Senaryo':<16} {'Yakit(L)':>10} {'CO2(kg)':>10} "
          f"{'Yakit TL':>12} {'Bekleme(s)':>10}")
    print(f"  {'-'*60}")
    
    for s in summary:
        fuel_l = float(s['total_fuel_litre'])
        co2_kg = float(s['total_co2_kg'])
        fuel_tl = fuel_l * BENZIN_TL
        wait_s = float(s['avg_waiting_s'])
        
        print(f"  {s['scenario']:<16} {fuel_l:>10.1f} {co2_kg:>10.1f} "
              f"{fuel_tl:>12,.0f} {wait_s:>10.1f}")
    
    # Kaos vs Standart farki
    s1a = next(s for s in summary if s['scenario'] == 'scenario_1a')
    s2b = next(s for s in summary if s['scenario'] == 'scenario_2b')
    
    fuel_diff = float(s2b['total_fuel_litre']) - float(s1a['total_fuel_litre'])
    co2_diff = float(s2b['total_co2_kg']) - float(s1a['total_co2_kg'])
    fuel_pct = (fuel_diff / float(s1a['total_fuel_litre'])) * 100
    
    print(f"\n  Kaos (2b) vs Standart (1a) FARKI:")
    print(f"    Ekstra yakit:  {fuel_diff:,.0f} L (+{fuel_pct:.0f}%)")
    print(f"    Ekstra CO2:    {co2_diff:,.1f} kg")
    print(f"    Ekstra maliyet: {fuel_diff * BENZIN_TL:,.0f} TL")


def main():
    print("\n" + "#"*60)
    print("  VERI ANALIZI VE GORSELLEŞTIRME")
    print("#"*60 + "\n")
    
    plot_1_fuel_comparison_bar()
    plot_2_co2_comparison_bar()
    plot_3_group_comparison()
    plot_4_time_series()
    plot_5_waiting_time()
    plot_6_cost_analysis()
    
    print_cost_table()
    
    print(f"\n  Tum grafikler: {PLOTS_DIR}/ klasorunde")
    print(f"\n{'#'*60}\n")


if __name__ == "__main__":
    main()

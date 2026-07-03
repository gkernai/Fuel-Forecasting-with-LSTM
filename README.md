Overview
This project models the "invisible costs" of urban traffic—specifically fuel consumption, CO2 emissions, and time loss—in the Kızılay-Sıhhiye-Tandoğan axis of Ankara. 
It utilizes the SUMO (Simulation of Urban Mobility) micro-simulation environment to capture dynamic traffic behavior and a PyTorch-based LSTM (Long Short-Term Memory) neural network to predict future fuel and emission metrics. 
The study directly compares standard traffic flows with chaos (match exits, accidents) and optimized green wave scenarios.  

FeaturesSUMO & TraCI Integration: Extracts micro-level, real-time metrics (speed, fuel, CO2, waiting time, halting vehicles) via the TraCI Python API.  
Comprehensive Scenario Analysis: Simulates 9 distinct scenarios, including morning/evening peaks, continuous congestion, accidents, and adaptive traffic light systems (TLS).  
Deep Learning Prediction: Features an advanced LSTM architecture that predicts total fuel consumption and CO2 emissions for the next timestep based on a 60-second historical window of traffic conditions.
Socio-Economic Cost Calculation: Converts emissions and time loss into real-world monetary values (TRY) to highlight the financial impact of urban congestion.

Simulation DetailsThe simulation network is built using OpenStreetMap data covering an approximately 1.5 km² area comprising Ankara's central business district.  
Edges (Road Segments): 1,389   Nodes (Intersections): 961   Traffic Lights (TLS): 32   Emission Engine: Fuel and CO2 calculations are computed by SUMO's internal HBEFA3 emission model.  

LSTM Model ArchitectureA multi-output LSTM model is trained on time-series data extracted from the standard and chaos scenarios.  
Input Features: Vehicle count, mean speed, halting vehicle count (Sequence Length: 60).  Output Targets: Total fuel consumption (ml/s), Total CO2 emission (mg/s).  Architecture: 2-layer LSTM (Hidden Size: 64, Dropout: 0.2) followed by Fully Connected (FC) layers.  
Optimization: Adam optimizer (LR: 0.001), MSE Loss.  Performance (Test Set): Achieved an RMSE of 7,826.05 ml/s for fuel consumption and 24,507.87 mg/s for CO2 emissions.  

Key FindingsThe Cost of Chaos: Continuous heavy traffic (Scenario 2b) resulted in a 49% increase in both fuel consumption and CO2 emissions compared to standard peak hour traffic.  
Accident Impact: A simulated accident (Scenario 2c) causing a lane closure at the 15-minute mark increased average waiting times by 6.5 times, peaking at 81.3 seconds per vehicle.  
Economic Toll: The chaos scenario generates an estimated 6.6 million TL in additional fuel costs per hour compared to standard traffic flow (calculated at 52 TL/L).  

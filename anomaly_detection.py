# anomaly_detection.py
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

def detect_anomalies(data, std_threshold=3.0):
    """
    Detects anomalies using a range-adaptive approach that explicitly 
    adjusts detection sensitivity based on the data range.
    
    Args:
        data (pd.DataFrame): DataFrame containing 'Frequency_Hz' and 'Power_dB/Hz'.
        std_threshold (float): Base threshold for standard deviation detection.
    
    Returns:
        pd.DataFrame: Original data with an additional 'Anomaly' column.
    """
    # Calculate data range
    power_range = data["Power_dB/Hz"].max() - data["Power_dB/Hz"].min()
    
    # Store info about the data range
    data.attrs['power_range'] = power_range
    
    # CRITICAL: Adjust contamination based on range
    # For small ranges (< 10 dB), use a much smaller contamination value
    if power_range < 10:
        contamination = 0.01  # Very few anomalies for narrow ranges
        # Also make the std threshold stricter for narrow ranges
        adjusted_std_threshold = std_threshold * 0.6  # Make threshold stricter (e.g., 1.8 σ instead of 3 σ)
    elif power_range < 20:
        contamination = 0.03  # Moderate anomalies for medium ranges
        adjusted_std_threshold = std_threshold * 0.8  # Slightly stricter
    else:
        contamination = 0.05  # More anomalies for wide ranges
        adjusted_std_threshold = std_threshold  # Keep original threshold
    
    # Store the adjusted parameters
    data.attrs['used_contamination'] = contamination
    data.attrs['used_std_threshold'] = adjusted_std_threshold
    
    # Normalize data
    scaler = StandardScaler()
    data["Power_Normalized"] = scaler.fit_transform(data[["Power_dB/Hz"]])
    
    # 1. Isolation Forest with adaptive contamination
    model = IsolationForest(contamination=contamination)
    data["IF_Anomaly"] = model.fit_predict(data[["Power_Normalized"]])
    
    # 2. Standard deviation with adaptive threshold
    mean = data["Power_dB/Hz"].mean()
    std = data["Power_dB/Hz"].std()
    data["STD_Anomaly"] = ((data["Power_dB/Hz"] > (mean + adjusted_std_threshold * std)) | 
                           (data["Power_dB/Hz"] < (mean - adjusted_std_threshold * std)))
    
    # 3. Combined approach, using explicit range-based scaling
    # For very narrow ranges, further reduce anomaly count by requiring both methods to agree
    if power_range < 8:
        # For very stable signals, require both methods to agree (logical AND)
        data["Anomaly"] = ((data["IF_Anomaly"] == -1) & (data["STD_Anomaly"] == True)).astype(int) * -2 + 1
    else:
        # For more variable signals, either method can flag (logical OR)
        data["Anomaly"] = ((data["IF_Anomaly"] == -1) | (data["STD_Anomaly"] == True)).astype(int) * -2 + 1
    
    # Store detection statistics
    data.attrs['if_anomaly_count'] = (data["IF_Anomaly"] == -1).sum()
    data.attrs['std_anomaly_count'] = data["STD_Anomaly"].sum()
    data.attrs['combined_anomaly_count'] = (data["Anomaly"] == -1).sum()
    
    return data
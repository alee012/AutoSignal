import streamlit as st
import pandas as pd
import os
import subprocess
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# --------------------------
# Function: Anomaly Detection
# --------------------------
def detect_anomalies(data, std_threshold=3.0):
    """
    Detects anomalies using a range-adaptive approach that explicitly 
    adjusts detection sensitivity based on the data range.
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


# --------------------------
# Function: Run Command & Check CSV
# --------------------------
def run_command_and_read_csv(command, csv_file):
    with st.spinner("🔍 Scanning frequencies..."):
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"❌ Command failed:\n```\n{result.stderr}\n```")
        return False
    if not os.path.exists(csv_file):
        st.error(f"❌ File not found: `{csv_file}`")
        return False
    return True


# --------------------------
# Configuration
# --------------------------
file_path = "./no_interfere.csv"  # Adjust path as needed
command = f"./rtl_power_fftw -f 442M:443M -b 512 -t 10 > {file_path}"
st.set_page_config(page_title="📡 SpectraShield", layout="wide")


# --------------------------
# Custom CSS (Updated Colors)
# --------------------------
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@100..900&display=swap');
        

        html, body, [class*="css"] {
            font-family: 'Lexend', sans-serif !important;
            background-color: #ffffff; /* White background */
            color: #ffffff; /* Dark gray text */
        }

        .main-title {
            font-size: 2.5rem;
            font-weight: 800;
            color: black; /* Blue title */
            letter-spacing: -1px;
            margin-top: -60px;
        }

        .subtitle {
            font-size: 1.1rem;
            color: #666666; /* Gray subtitle */
            margin-top: -10px;
        }

        .stButton > button {
            background: #001f3f;
            color: white;
            font-weight: 600;
            padding: 0.5rem 4rem;
            border-color: rgb(226, 154, 69);
            border-radius: 10px;
            transition: all 0.2s ease-in-out;
            margin-left: 20px
        }


        .section-title {
            font-size: 1.4rem;
            color: rgb(217, 142, 58) /* Orange section titles */
        }

        .logo {
            font-size: 2.3rem;
            font-weight: bold;
            margin-top: -0.5rem;
            color: rgb(217, 142, 58) /* Orange section titles */
        }


        .card-container {
            display: flex;
            justify-content: space-between;
            gap: 1.5rem;
            margin-top: 2rem;
            margin-bottom: 2rem;
            flex-wrap: wrap; /* So they wrap on small screens */
        }

        .data-card {
            background: white;
            border: 1px solid #e0e0e0;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.05);
            flex: 1;
            min-width: 200px;
            max-width: 100%;
            text-align: center;
            color: black;
        }

        .metric-card {
            background: white;
            border: 1px solid #e0e0e0;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.05);
            flex: 1;
            min-width: 180px;
            text-align: center;
            color: black;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #001f3f;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #666;
            margin-top: -5px;
        }

        .sidebar .sidebar-content {
            background-color: #001f3f; /* Navy blue sidebar */
            color: #ffffff; /* White text for better contrast */
        }


        .material-symbols-outlined {
            font-variation-settings:
            'FILL' 0,
            'wght' 400,
            'GRAD' 0,
            'opsz' 24
        }

        .material-symbols-outlined.orange-icon {
            font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
            vertical-align: middle;
            color: rgb(217, 142, 58); /* Your existing orange */
            font-size: 2.5rem;
            margin-right: 8px;
        }
        .logo-title {
            font-size: 2.3rem;
            color: rgb(217, 142, 58);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            margin-top: -15px
        }
        
        .anomaly-section {
            margin-top: 2rem;
            background: white;
            border: 1px solid #e0e0e0;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.05);
            color: black;
        }
        
        .anomaly-header {
            font-size: 1.4rem;
            font-weight: 600;
            color: #001f3f;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
        }
        
        .info-text {
            color: #666;
            font-size: 0.95rem;
        }
        
        .range-indicator {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 4px;
            font-weight: 600;
            margin-right: 0.5rem;
        }
        
        .stable-range {
            background-color: #d4edda;
            color: #155724;
        }
        
        .moderate-range {
            background-color: #fff3cd;
            color: #856404;
        }
        
        .wide-range {
            background-color: #f8d7da;
            color: #721c24;
        }

    </style>

    
""", unsafe_allow_html=True)

st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #001f3f;
        color: #ffffff;
        border-top-right-radius: 20px;
        border-bottom-right-radius: 20px;
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
        padding: 10px;
        box-shadow: 4px 0 12px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)


# --------------------------
# Header
# --------------------------
st.markdown('<div class="main-title">Dashboard</div>', unsafe_allow_html=True)
st.markdown("---")

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    st.markdown('''
    <div class="logo-title">
        <span class="material-symbols-outlined orange-icon">settings_input_antenna</span>
        SpectraShield
    </div>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="section-title">🛠️ Monitor</div>', unsafe_allow_html=True)
    
    # Toggle for anomaly detection
    enable_anomaly_detection = st.checkbox("🔍 Enable Anomaly Detection", value=True)
    
    st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
    if st.button("🔍 Start Scan"):
        if run_command_and_read_csv(command, file_path):
            st.success("✅ Scan complete!")
        else:
            st.error("⚠️ Scan failed. Check your setup.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">📘 Info</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="color:rgb(124, 124, 161); font-size: 0.95rem;">
        <strong>SpectraShield</strong> lets you visualize RF power scans in real-time.
        <br><br>
        <strong>Details:</strong>
        <ul>
            <li>Frequency: <strong>442–443 MHz</strong></li>
            <li>Power: <strong>dB/Hz</strong></li>
            <li>Captured using: <code>rtl_power_fftw</code></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --------------------------
# Main Content
# --------------------------
if os.path.exists(file_path):
    try:
        df = pd.read_csv(
            file_path,
            comment='#',
            header=None,
            names=["Frequency_Hz", "Power_dB/Hz"],
            delim_whitespace=True
        )
    except Exception as e:
        st.error(f"❌ Failed to load CSV: {e}")
        df = pd.DataFrame()

    if not df.empty:
        # Calculate data range for cards
        power_min = df["Power_dB/Hz"].min()
        power_max = df["Power_dB/Hz"].max()
        power_range = power_max - power_min
        
        # Determine signal stability classification
        if power_range < 10:
            range_color = "green"
            range_description = "Stable"
            range_class = "stable-range"
        elif power_range < 20:
            range_color = "orange"
            range_description = "Moderate"
            range_class = "moderate-range"
        else:
            range_color = "red"
            range_description = "Highly Variable"
            range_class = "wide-range"
        
        # Device info cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="data-card"><strong style="font-size: 25px">RTL-SDR v3</strong><br>Device</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="data-card"><strong style="font-size: 25px">442–443 MHz</strong><br>Frequency</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="data-card"><strong style="font-size: 25px">10s</strong><br>Run Time</div>', unsafe_allow_html=True)
            
        with col4:
            st.markdown(f'<div class="data-card"><strong style="font-size: 25px"><span class="range-indicator {range_class}">{range_description}</span></strong><br>Signal Stability</div>', unsafe_allow_html=True)

        # Run anomaly detection if enabled
        if enable_anomaly_detection:
            df = detect_anomalies(df)
            anomalies = df[df["Anomaly"] == -1]  # -1 indicates an anomaly
        
        # Create main plot
        fig = go.Figure()

        # Add main spectrum line
        fig.add_trace(go.Scatter(
            x=df["Frequency_Hz"],
            y=df["Power_dB/Hz"],
            mode='lines',
            line=dict(color="#1a73e8", width=2),
            name="Power"
        ))
        
        # Add anomalies if enabled and found
        if enable_anomaly_detection and not anomalies.empty:
            fig.add_trace(go.Scatter(
                x=anomalies["Frequency_Hz"],
                y=anomalies["Power_dB/Hz"],
                mode='markers',
                name='Anomaly',
                marker=dict(color='red', size=8, symbol='circle')
            ))

        # Update layout
        fig.update_layout(
            title={
                'text': "RF Power Spectrum",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24)
            },
            xaxis_title="Frequency (Hz)",
            yaxis_title="Power (dB/Hz)",
            template="plotly_white",
            height=500,
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # Display plot
        st.plotly_chart(fig, use_container_width=True)
        
        # Anomaly Analysis Section
        if enable_anomaly_detection:
            st.markdown('<div class="anomaly-section">', unsafe_allow_html=True)
            
            if not anomalies.empty:
                st.markdown('<div class="anomaly-header">🚨 Anomaly Analysis</div>', unsafe_allow_html=True)
                
                # Display detection method information
                st.markdown("<strong>Detection Settings</strong>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-text">
                    Power Range: <strong>{power_range:.2f} dB</strong> ({power_min:.2f} to {power_max:.2f} dB/Hz)<br>
                    Method: <strong>{'Both methods must agree (AND)' if power_range < 8 else 'Either method can flag (OR)'}</strong><br>
                    Contamination Rate: <strong>{df.attrs.get('used_contamination', 'N/A')}</strong><br>
                    Standard Deviation Threshold: <strong>{df.attrs.get('used_std_threshold', 'N/A')}σ</strong>
                </div>
                """, unsafe_allow_html=True)
                
                # Display metrics
                st.markdown("<br><strong>Anomaly Metrics</strong>", unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">{len(anomalies)}</div>
                        <div class="metric-label">Total Anomalies</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">{df.attrs.get('if_anomaly_count', 0)}</div>
                        <div class="metric-label">Isolation Forest</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">{df.attrs.get('std_anomaly_count', 0)}</div>
                        <div class="metric-label">Std Deviation</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col4:
                    anomaly_density = len(anomalies) / power_range if power_range > 0 else 0
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">{anomaly_density:.2f}</div>
                        <div class="metric-label">Anomalies per dB</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                # Create a Plotly histogram for anomaly distribution
                if len(anomalies) > 1:  # Only show histogram if we have multiple anomalies
                    anomaly_hist = go.Figure()
                    anomaly_hist.add_trace(go.Histogram(
                        x=anomalies["Power_dB/Hz"],
                        nbinsx=10,
                        marker_color='red',
                        opacity=0.7
                    ))
                    anomaly_hist.update_layout(
                        title="Anomaly Power Distribution",
                        xaxis_title="Power (dB/Hz)",
                        yaxis_title="Count",
                        template="plotly_white",
                        height=300,
                        margin=dict(l=40, r=40, t=60, b=40),
                    )
                    st.plotly_chart(anomaly_hist, use_container_width=True)
                
                # Display anomaly data table
                st.markdown("<br><strong>Anomaly Details</strong>", unsafe_allow_html=True)
                st.dataframe(anomalies[["Frequency_Hz", "Power_dB/Hz"]], use_container_width=True)
            
            else:
                st.markdown('<div class="anomaly-header">✅ Anomaly Analysis</div>', unsafe_allow_html=True)
                st.info("No anomalies detected in the current scan.")
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close anomaly section
            
    else:
        st.warning("⚠️ No data found in CSV.")
else:
    st.info(f"📂 Awaiting scan... No file found at: `{file_path}`")
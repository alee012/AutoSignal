import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import subprocess

# --------------------------
# Function: Run Command & Check CSV
# --------------------------
def run_command_and_read_csv(command, csv_file):
    """
    Runs the provided command to generate the CSV file.
    Returns True if the command runs successfully and the CSV file exists.
    """
    with st.spinner("Running RTL command..."):
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"Error running command: {result.stderr}")
        return False
    if not os.path.exists(csv_file):
        st.error(f"CSV file '{csv_file}' not found after running command.")
        return False
    return True

# --------------------------
# File Path & Command
# --------------------------
# Update these as needed
file_path = "./transmitting.csv"
command = f"./rtl_power_fftw -f 442M:443M -b 512 -t 10 > {file_path}"

# --------------------------
# Page Configuration
# --------------------------
st.set_page_config(page_title="📡 Frequency vs Power Plot", layout="wide")

# --------------------------
# Main Title and Description
# --------------------------
st.markdown("""
    <style>
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
        }
        .subtitle {
            font-size: 1.2rem;
            margin-top: -10px;
        }
        .stButton > button {
            background-color: #4CAF50;
            color: white;
        }
        .sidebar-title {
            font-size: 1.2rem;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 Frequency vs. Power Plot</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Visualizing a Power Spectrum from <strong>400 MHz</strong> to <strong>410 MHz</strong></div>', unsafe_allow_html=True)
st.markdown("""---""")

# --------------------------
# Sidebar UI
# --------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">Hardware Manager:</div>', unsafe_allow_html=True)
    
    # Button to run the RTL command
    if st.button("Scan"):
        if run_command_and_read_csv(command, file_path):
            st.success("Command executed successfully and results are ready!")


# --------------------------
# File Loading & Plotting
# --------------------------
if os.path.exists(file_path):
    try:
        # Load the file, skipping comments and using whitespace as the delimiter
        df = pd.read_csv(
            file_path,
            comment='#',
            header=None,
            names=["Frequency_Hz", "Power_dB/Hz"],
            delim_whitespace=True
        )
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        df = pd.DataFrame()
    
    if df.empty:
        st.error("No valid data found in the file.")
    else:
        # Plotting
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df["Frequency_Hz"], df["Power_dB/Hz"], linewidth=1.2, color="blue")
        ax.set_xlabel("Frequency (Hz)", fontsize=12)
        ax.set_ylabel("Power Spectral Density (dB/Hz)", fontsize=12)
        ax.set_title("Power vs Frequency", fontsize=14, weight='bold')
        ax.grid(True, linestyle='--', alpha=0.5)
        # Set y-axis max to 0 while auto-adjusting the bottom
        ax.set_ylim(bottom=df["Power_dB/Hz"].min(), top=0)
        st.pyplot(fig)

        st.markdown("""---""")

        # Additional Details
        st.markdown("### 📘 Overview & Key Components")
        st.markdown("""
        - **Overview**  
        This app displays a real power spectrum over a frequency range from **400 MHz** to **410 MHz**, using data captured via RTL-SDR tools.
        
        - **Key Components**  
            - 📡 **Frequency Input**: Loaded from a CSV file with actual frequency values.  
            - ⚡ **Power Measurement**: Shown in dB/Hz, parsed from SDR scan results.  
            - 📈 **Matplotlib Plot**: Styled with clear labels, grid, and interactive features.
        """)
else:
    st.error(f"❌ File not found at: `{file_path}`")

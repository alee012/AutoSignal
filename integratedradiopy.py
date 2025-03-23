import streamlit as st
import pandas as pd
import os
import subprocess
import plotly.graph_objects as go


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
file_path = "/Users/vivekrevankar/Downloads/transmitting.csv"
command = f"./rtl_power_fftw -f 442M:443M -b 512 -t 10 > {file_path}"
st.set_page_config(page_title="📡 SpectraShield", layout="wide")



# --------------------------
# Custom CSS (Updated Colors)
# --------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@100..900&display=swap');

        html, body, [class*="css"] {
            font-family: 'Lexend', sans-serif !important;
            background-color: #ffffff; /* White background */
            color: #ffffff; /* Dark gray text */
        }

        .main-title {
            font-size: 2.8rem;
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
            background: rgb(226, 154, 69);
            color: white;
            font-weight: 600;
            padding: 0.5rem 4rem;
            border: none;
            border-radius: 10px;
            transition: all 0.2s ease-in-out;
            margin-left: 20px
        }


        .section-title {
            font-size: 1.4rem;
            font-weight: bold;
            margin-top: 2rem;
            color: rgb(217, 142, 58) /* Blue section titles */
        }

        .logo {
            font-size: 2.3rem;
            font-weight: bold;
            margin-top: 2rem;
            color: rgb(217, 142, 58) /* Blue section titles */
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



        .sidebar .sidebar-content {
            background-color: #001f3f; /* Navy blue sidebar */
            color: #ffffff; /* White text for better contrast */
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
    st.markdown('<div class="logo">SpectraShield</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">🛠️ Monitor</div>', unsafe_allow_html=True)

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
        
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown('<div class="data-card"><strong style="font-size: 25px">RTL-SDR v3</strong><br>Device</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="data-card"><strong style="font-size: 25px">442–443 MHz</strong><br>Frequency</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="data-card"><strong style="font-size: 25px">10s</strong><br>Run Time</div>', unsafe_allow_html=True)

        st.markdown("---")


        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df["Frequency_Hz"],
            y=df["Power_dB/Hz"],
            mode='lines',
            line=dict(color="#1a73e8", width=2),
            name="Power"
        ))

        fig.update_layout(
            title="Power vs Frequency",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Power (dB/Hz)",
            template="plotly_white",
            height=500,
            margin=dict(l=40, r=40, t=60, b=40),
        )

        fig.update_yaxes(range=[df["Power_dB/Hz"].min(), 0])

        st.plotly_chart(fig, use_container_width=True)


        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ No data found in CSV.")
else:
    st.info(f"📂 Awaiting scan... No file found at: `{file_path}`")

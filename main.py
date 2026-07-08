import streamlit as st
from f1_23_data import TelemetrySession, plot_telemetry, ip_address

st.set_page_config("Formula Coach")
st.title("Formula Coach")
text = f"Before you start, go to Settings -> Telemetry Settings, and insert the following values: \nUDP IP Address: {ip_address}\nUDP Port: 27000\nKeep in mind that NO data, for any reason whatsoever, is stored in our files. This is so that the UDP telemetry can send the input data to the program for it to work."

st.text(text)

if "running" not in st.session_state:
    st.session_state.running = False
    st.session_state.session = None
    st.session_state.data = None

col1, col2 = st.columns(2)

with col1:
    if st.button("Start") and not st.session_state.running:
        st.session_state.session = TelemetrySession()
        st.session_state.running = True
        st.rerun()

with col2:
    if st.button("Stop") and st.session_state.running and st.session_state.session is not None:
        data = st.session_state.session.stop()
        st.session_state.data = data
        st.session_state.running = False
        st.rerun()

if st.session_state.running:
    st.info("Collecting telemetry... Press Stop to finish.")

if "data" in st.session_state and st.session_state.data is not None:
    fig = plot_telemetry(st.session_state.data)
    st.pyplot(fig)

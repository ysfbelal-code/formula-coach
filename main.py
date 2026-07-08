import streamlit as st
from data_backend import start_collection, stop_collection, pop_data, plot_telemetry, ip_address

st.set_page_config("Formula Coach")
st.title("Formula Coach")

st.text(
    f"Before you start, go to Settings -> Telemetry Settings, and insert the following values:\n"
    f"UDP IP Address: {ip_address}\nUDP Port: 27000\n\n"
    "No data is stored. UDP telemetry sends input data to this program only."
)

if "active_lap_telemetry" not in st.session_state:
    st.session_state.active_lap_telemetry = False

col1, col2 = st.columns(2)

with col1:
    if st.button("Start") and not st.session_state.active_lap_telemetry:
        start_collection()
        st.session_state.active_lap_telemetry = True
        st.rerun()

with col2:
    if st.button("Stop") and st.session_state.active_lap_telemetry:
        stop_collection()
        st.session_state.active_lap_telemetry = False
        st.rerun()

if st.session_state.active_lap_telemetry:
    st.info("Collecting telemetry... Press Stop to finish.")
else:
    data = pop_data()
    if data is not None:
        fig = plot_telemetry(data)
        st.pyplot(fig)

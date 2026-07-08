import threading
import streamlit as st
from f1_23_data import start_f123_lap_telemetry, plot_telemetry, get_udp_data

st.set_page_config("Formula Coach")
st.title("Formula Coach")
udp_details = get_udp_data()
ip_address = udp_details[0]
port = udp_details[1]

text = ("Before you start, go to Settings -> Telemetry Settings, and insert the following value:"
    f"\nUDP IP Address: {ip_address}\n"
    f"UDP Port: {port}\n", 
    "Keep in mind that NO data, for any reason whatsoever, is stored in our files."
    "This is so that the UDP telemetry can send the input data to the program for it to work."
)

st.text(text)
if "stop_event" not in st.session_state:
    st.session_state.stop_event = threading.Event()
    st.session_state.running = False
    st.session_state.data = None

col1, col2 = st.columns(2)
with col1:
    if st.button("Start"):
        st.session_state.stop_event.clear()
        st.session_state.running = True
        st.session_state.data = None
        st.rerun()

with col2:
    if st.button("Stop"):
        st.session_state.stop_event.set()

if st.session_state.running:
    with st.spinner("Collecting telemetry... Press Stop to finish."):
        st.session_state.data = start_f123_lap_telemetry(st.session_state.stop_event, ip_address=ip_address, port=port)
        st.session_state.running = False
        st.rerun()

if st.session_state.data is not None:
    fig = plot_telemetry(st.session_state.data)
    st.pyplot(fig)

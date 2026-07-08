import threading
import socket
import streamlit as st
import matplotlib.pyplot as plt

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

if "active" not in st.session_state:
    st.session_state.active = False
    st.session_state.data = None
    st.session_state.listener = None
    st.session_state.thread = None
    st.session_state.evt = None
    st.session_state.result = None


def backend_available():
    try:
        from f1_23_telemetry.listener import TelemetryListener
        return True
    except ImportError:
        return False


def start():
    from f1_23_telemetry.listener import TelemetryListener
    from f1_23_telemetry.appendices import TRACK_IDS

    evt = threading.Event()
    result = [None]

    def collect():
        speed = []
        throttle = []
        brake = []
        steering = []
        g_force_lat = []
        lap_starts = []
        last_lap = 0

        result[0] = {
            "speed": speed, "throttle": throttle, "brake": brake,
            "steering": steering, "g_force_lat": g_force_lat, "lap_starts": lap_starts,
        }

        try:
            listener = st.session_state.listener
            while not evt.is_set():
                try:
                    packet = listener.get()
                except OSError:
                    break

                pid = packet.header.packet_id

                if pid == 1:
                    print(f"Track: {TRACK_IDS.get(packet.track_id, 'Unknown')}")
                elif pid == 2:
                    idx = packet.header.player_car_index
                    lap = packet.lap_data[idx].current_lap_num
                    if lap != last_lap:
                        lap_starts.append(len(speed))
                        print(f"Lap {lap} start")
                        last_lap = lap
                elif pid == 0:
                    idx = packet.header.player_car_index
                    g_force_lat.append(packet.car_motion_data[idx].g_force_lateral)
                elif pid == 6:
                    idx = packet.header.player_car_index
                    t = packet.car_telemetry_data[idx]
                    speed.append(t.speed)
                    throttle.append(int(t.throttle * 100))
                    brake.append(int(t.brake * 100))
                    steering.append(t.steer)
        except Exception:
            pass

        result[0] = {
            "speed": speed, "throttle": throttle, "brake": brake,
            "steering": steering, "g_force_lat": g_force_lat, "lap_starts": lap_starts,
        }

    st.session_state.listener = TelemetryListener(port=27000, host="0.0.0.0")
    st.session_state.evt = evt
    st.session_state.result = result
    st.session_state.thread = threading.Thread(target=collect, daemon=True)
    st.session_state.thread.start()
    st.session_state.data = None
    st.session_state.active = True


def stop():
    if st.session_state.evt is not None:
        st.session_state.evt.set()
    if st.session_state.listener is not None:
        try:
            st.session_state.listener.socket.close()
        except OSError:
            pass
    if st.session_state.thread is not None:
        st.session_state.thread.join()
    if st.session_state.result is not None:
        st.session_state.data = st.session_state.result[0]
    st.session_state.active = False


def plot(data):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    ax1.plot(data["speed"], label="Speed (km/h)", color="cyan")
    ax1.plot(data["throttle"], label="Throttle (%)", color="gold")
    ax1.plot(data["brake"], label="Brake (%)", color="red")
    for i, ls in enumerate(data["lap_starts"]):
        ax1.axvline(x=ls, color="gray", linestyle="--", alpha=0.5)
        ax1.text(ls, ax1.get_ylim()[1], f"Lap {i+1}", rotation=90, va="top", fontsize=8, color="gray")
    ax1.set_ylabel("Value")
    ax1.legend()
    ax1.set_title("Car Controls")

    ax2.plot(data["steering"], label="Steering", color="green")
    ax2.plot(data["g_force_lat"], label="Lateral G", color="purple")
    for i, ls in enumerate(data["lap_starts"]):
        ax2.axvline(x=ls, color="gray", linestyle="--", alpha=0.5)
    ax2.set_ylabel("Value")
    ax2.set_xlabel("Sample")
    ax2.legend()
    ax2.set_title("Steering & Cornering")

    plt.tight_layout()
    return fig


st.set_page_config("Formula Coach")
st.title("Formula Coach")

st.text(
    f"Settings -> Telemetry Settings:\n"
    f"UDP IP Address: {ip_address}\nUDP Port: 27000\n"
    "No data stored."
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Start") and not st.session_state.active:
        if not backend_available():
            st.error("f1_23_telemetry not installed. pip install f1-23-telemetry")
        else:
            start()
            st.rerun()

with col2:
    if st.button("Stop") and st.session_state.active:
        stop()
        st.rerun()

if st.session_state.active:
    st.info("Collecting telemetry... Press Stop to finish.")
elif st.session_state.data is not None:
    st.pyplot(plot(st.session_state.data))

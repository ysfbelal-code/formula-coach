import threading
import socket
import streamlit as st
import matplotlib.pyplot as plt

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

_backend = None
_running = False
_thread = None
_listener = None
_data = None


def backend_available():
    global _backend
    if _backend is None:
        try:
            from f1_23_telemetry.listener import TelemetryListener
            _backend = True
        except ImportError:
            _backend = False
    return _backend


def start(port=65535, host=ip_address):
    global _running, _thread, _listener, _data
    if _running:
        return
    if not backend_available():
        raise RuntimeError("f1_23_telemetry not installed")
    from f1_23_telemetry.listener import TelemetryListener
    from f1_23_telemetry.appendices import TRACK_IDS
    _data = None
    _listener = TelemetryListener(port=port, host=host)
    _running = True
    _thread = threading.Thread(target=lambda: _run(TRACK_IDS), daemon=True)
    _thread.start()


def stop():
    global _running, _listener, _thread, _data
    if not _running:
        return
    _running = False
    if _listener is not None:
        _listener.socket.close()
    if _thread is not None:
        _thread.join()


def get_data():
    return _data

def _run(track_ids):
    global _data

    speed, throttle, brake, steering, g_force_lat, lap_starts = ([] for _ in range(6))
    last_lap = 0

    try:
        while _running:
            try:
                packet = _listener.get()
            except OSError:
                break

            pid = packet.header.packet_id

            if pid == 1:
                print(f"Track: {track_ids.get(packet.track_id, 'Unknown')}")
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

    _data = {
        "speed": speed, "throttle": throttle, "brake": brake,
        "steering": steering, "g_force_lat": g_force_lat, "lap_starts": lap_starts,
    }


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
    f"UDP IP Address: {ip_address}\nUDP Port: 65535\n"
    "No data stored."
)

if "active_lap_telemetry" not in st.session_state:
    st.session_state.active_lap_telemetry = False

col1, col2 = st.columns(2)

with col1:
    if st.button("Start") and not st.session_state.active_lap_telemetry:
        if not backend_available():
            st.error("f1_23_telemetry not installed. pip install f1-23-telemetry")
        else:
            start()
            st.session_state.active_lap_telemetry = True
            st.rerun()

with col2:
    if st.button("Stop") and st.session_state.active_lap_telemetry:
        stop()
        st.session_state.active_lap_telemetry = False

if st.session_state.active_lap_telemetry:
    st.info("Collecting telemetry... Press Stop to finish.")
else:
    d = get_data()
    if d is not None:
        st.pyplot(plot(d))

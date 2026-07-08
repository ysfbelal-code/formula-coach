import socket
import threading
from f1_23_telemetry.listener import TelemetryListener
from f1_23_telemetry.appendices import TRACK_IDS
import matplotlib.pyplot as plt

def get_udp_data() -> tuple:
    hostname = socket.gethostname()
    IP_ADDRESS = socket.gethostbyname(hostname)
    UDP_PORT = 1000
    return IP_ADDRESS, UDP_PORT


def start_f123_lap_telemetry(stop_event: threading.Event, ip_address: str, port: int):
    speed = []
    throttle = []
    brake = []
    steering = []
    g_force_lat = []
    lap_starts = []
    last_lap = 0

    listener = TelemetryListener(port=port, host=ip_address)
    print("Listening for F1 23 telemetry packets...")

    while not stop_event.is_set():
        packet = listener.get()
        packet_id = packet.header.packet_id

        if packet_id == 1:
            track = TRACK_IDS.get(packet.track_id, "Unknown")
            print(f"Track: {track} (id={packet.track_id})")

        if packet_id == 2:
            player_car_idx = packet.header.player_car_index
            lap = packet.lap_data[player_car_idx].current_lap_num
            if lap != last_lap:
                lap_starts.append(len(speed))
                print(f"Lap {lap} start")
                last_lap = lap

        if packet_id == 0:
            player_car_idx = packet.header.player_car_index
            g_force_lat.append(packet.car_motion_data[player_car_idx].g_force_lateral)

        if packet_id == 6:
            player_car_idx = packet.header.player_car_index
            player_telemetry = packet.car_telemetry_data[player_car_idx]

            speed.append(player_telemetry.speed)
            throttle.append(int(player_telemetry.throttle * 100))
            brake.append(int(player_telemetry.brake * 100))
            steering.append(player_telemetry.steer)

    print("\nTelemetry collection stopped.")

    data = {
        "speed": speed,
        "throttle": throttle,
        "brake": brake,
        "steering": steering,
        "g_force_lat": g_force_lat,
        "lap_starts": lap_starts,
    }
    return data


def plot_telemetry(data):
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

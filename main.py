import socket
from f1_23_telemetry.listener import TelemetryListener
from f1_23_telemetry.appendices import TRACK_IDS
import matplotlib.pyplot as plt

hostname = socket.gethostname()
IP_ADDRESS = socket.gethostbyname(hostname)
UDP_PORT = 65535

speed = []
throttle = []
brake = []
steering = []
g_force_lat = []
lap_starts = []
last_lap = 0

listener = TelemetryListener(port=UDP_PORT, host=IP_ADDRESS)
print("Listening for F1 23 telemetry packets...")

try:
    while True:
        packet = listener.get()
        packet_id = packet.header.packet_id

        if packet_id == 1:
            track = TRACK_IDS.get(packet.track_id, "Unknown")
            print(f"Track: {track}")

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

        if packet_id == 5:
            player_car_idx = packet.header.player_car_index
            s = packet.car_setups[player_car_idx]
            print(
                f"Setup — Wing: {s.front_wing}/{s.rear_wing}  "
                f"Diff: {s.on_throttle}/{s.off_throttle}  "
                f"Camber: {s.front_camber:.1f}/{s.rear_camber:.1f}  "
                f"Toe: {s.front_toe:.1f}/{s.rear_toe:.1f}  "
                f"Susp: {s.front_suspension}/{s.rear_suspension}  "
                f"ARB: {s.front_anti_roll_bar}/{s.rear_anti_roll_bar}  "
                f"Height: {s.front_suspension_height}/{s.rear_suspension_height}  "
                f"Brake: {s.brake_pressure}%/{s.brake_bias}%  "
                f"Tyres(PSI): {s.front_left_tyre_pressure:.1f}/{s.front_right_tyre_pressure:.1f}/"
                f"{s.rear_left_tyre_pressure:.1f}/{s.rear_right_tyre_pressure:.1f}  "
                f"Ballast: {s.ballast}  Fuel: {s.fuel_load:.1f}"
            )
            
        if packet_id == 6:
            player_car_idx = packet.header.player_car_index
            t = packet.car_telemetry_data[player_car_idx]
            speed.append(t.speed)
            throttle.append(int(t.throttle * 100))
            brake.append(int(t.brake * 100))
            steering.append(t.steer)

except KeyboardInterrupt:
    print("\nStopping. Plotting...")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    ax1.plot(speed, label="Speed (km/h)", color="cyan")
    ax1.plot(throttle, label="Throttle (%)", color="gold")
    ax1.plot(brake, label="Brake (%)", color="red")
    for i, ls in enumerate(lap_starts):
        ax1.axvline(x=ls, color="gray", linestyle="--", alpha=0.5)
        ax1.text(ls, ax1.get_ylim()[1], f"Lap {i+1}", rotation=90, va="top", fontsize=8, color="gray")
    ax1.set_ylabel("Value")
    ax1.legend()
    ax1.set_title("Car Controls")

    ax2.plot(steering, label="Steering", color="green")
    ax2.plot(g_force_lat, label="Lateral G", color="purple")
    for i, ls in enumerate(lap_starts):
        ax2.axvline(x=ls, color="gray", linestyle="--", alpha=0.5)
    ax2.set_ylabel("Value")
    ax2.set_xlabel("Sample")
    ax2.legend()
    ax2.set_title("Steering & Cornering")

    plt.tight_layout()
    plt.show()

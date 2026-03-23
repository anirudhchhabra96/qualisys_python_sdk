"""
Streaming 6DoF from QTM with real-time X-Y plot
"""

import argparse
import asyncio
import threading
import xml.etree.ElementTree as ET
from collections import deque

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import qtm_rt

MAXLEN = 500
xs, ys = deque(maxlen=MAXLEN), deque(maxlen=MAXLEN)

def create_body_index(xml_string):
    xml = ET.fromstring(xml_string)
    return {body.text.strip(): i for i, body in enumerate(xml.findall("*/Body/Name"))}

def body_enabled_count(xml_string):
    xml = ET.fromstring(xml_string)
    return sum(e.text == "true" for e in xml.findall("*/Body/Enabled"))

async def main(qtm_file=None, wanted_body="beatle1"):
    connection = await qtm_rt.connect("127.0.0.1")
    if connection is None:
        print("Failed to connect")
        return

    async with qtm_rt.TakeControl(connection, "password"):
        if qtm_file:
            await connection.load(qtm_file)
            await connection.start(rtfromfile=True)
        else:
            await connection.new()

    xml_string = await connection.get_parameters(parameters=["6d"])
    body_index = create_body_index(xml_string)
    print("{} of {} 6DoF bodies enabled".format(body_enabled_count(xml_string), len(body_index)))

    def on_packet(packet):
        _, bodies = packet.get_6d()
        if wanted_body in body_index:
            position, _ = bodies[body_index[wanted_body]]
            xs.append(position.x)
            ys.append(position.y)

    await connection.stream_frames(components=["6d"], on_packet=on_packet)
    # keep the event loop alive so callbacks keep firing
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream 6DoF data from QTM")
    parser.add_argument("--file", metavar="PATH")
    parser.add_argument("--body", default="beatle1")
    args = parser.parse_args()

    threading.Thread(
        target=lambda: asyncio.run(main(args.file, args.body)), daemon=True
    ).start()

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.suptitle(f"X-Y position — {args.body}")
    (trail,) = ax.plot([], [], lw=1, alpha=0.5)
    (dot,) = ax.plot([], [], "o", ms=7)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linewidth=0.5)
    ax.set_xlim(-3000, 3000)
    ax.set_ylim(0,3000)

    def update(_):
        if not xs:
            return trail, dot
        x, y = list(xs), list(ys)
        trail.set_data(x, y)
        dot.set_data([x[-1]], [y[-1]])
        # ax.relim()
        # ax.autoscale_view()
        return trail, dot

    ani = animation.FuncAnimation(fig, update, interval=50, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.show()
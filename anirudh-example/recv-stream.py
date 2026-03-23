# # pip install qtm-rt
# import asyncio, qtm_rt

# def on_packet(packet):
#     header, markers = packet.get_3d_markers()
#     for m in markers:
#         print(m)

# async def main():
#     conn = await qtm_rt.connect("192.168.0.198")
#     if conn is None:
#         return
#     await conn.stream_frames(components=["3d"], on_packet=on_packet)

# asyncio.run(main())

# import asyncio, qtm_rt, pyqtgraph as pg
# import pyqtgraph.opengl as gl
# import numpy as np
# from pyqtgraph.Qt import QtWidgets
# import sys, threading

# app = QtWidgets.QApplication(sys.argv)
# view = gl.GLViewWidget()
# view.show()
# scatter = gl.GLScatterPlotItem(color=(1,1,0,1), size=10)
# view.addItem(scatter)

# def on_packet(packet):
#     _, markers = packet.get_3d_markers()
#     if not markers: return
#     pts = np.array([[m.x, m.y, m.z] for m in markers])
#     scatter.setData(pos=pts)

# async def stream():
#     conn = await qtm_rt.connect("192.168.0.198")
#     if conn is None: return
#     await conn.stream_frames(components=["3d"], on_packet=on_packet)

# threading.Thread(target=asyncio.run, args=(stream(),), daemon=True).start()
# app.exec()

import asyncio, qtm_rt
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
scat = None

def on_packet(packet):
    global scat
    _, markers = packet.get_3d_markers()
    if not markers: return
    x, y, z = zip(*[(m.x, m.y, m.z) for m in markers])
    if scat: scat.remove()
    scat = ax.scatter(x, y, z)
    plt.pause(0.001)

async def main():
    conn = await qtm_rt.connect("192.168.0.198")
    if conn is None: return
    await conn.stream_frames(components=["3d"], on_packet=on_packet)
    await asyncio.sleep(float('inf'))  # keep alive

plt.ion()
asyncio.run(main())

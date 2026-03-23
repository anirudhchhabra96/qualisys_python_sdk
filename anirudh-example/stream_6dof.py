"""
    Streaming 6Dof from QTM
"""

import argparse
import asyncio
import xml.etree.ElementTree as ET

import qtm_rt

def create_body_index(xml_string):
    """ Extract a name to index dictionary from 6dof settings xml """
    xml = ET.fromstring(xml_string)

    body_to_index = {}
    for index, body in enumerate(xml.findall("*/Body/Name")):
        body_to_index[body.text.strip()] = index

    return body_to_index

def body_enabled_count(xml_string):
    xml = ET.fromstring(xml_string)
    return sum(enabled.text == "true" for enabled in xml.findall("*/Body/Enabled"))

async def main(qtm_file=None):

    # Connect to qtm
    connection = await qtm_rt.connect("127.0.0.1") # since the cameras are connected to local PC

    # Connection failed?
    if connection is None:
        print("Failed to connect")
        return

    # Take control of qtm, context manager will automatically release control after scope end
    async with qtm_rt.TakeControl(connection, "password"):

        if qtm_file:
            # File replay
            await connection.load(qtm_file)
            await connection.start(rtfromfile=True)
        else:
            # Real-time: start a new live measurement
            await connection.new()

            # the following is only needed if you want to start a new measurement, better way is to start the capture on software and then run this file
            # await connection.start()

    # Get 6dof settings from qtm
    xml_string = await connection.get_parameters(parameters=["6d"])
    body_index = create_body_index(xml_string)

    print("{} of {} 6DoF bodies enabled".format(body_enabled_count(xml_string), len(body_index)))

    # this is the rigid body you want to detect, put this into a list if you want multiple bodies
    wanted_body = "beatle-1"

    def on_packet(packet):
        info, bodies = packet.get_6d()
        print(
            "Framenumber: {} - Body count: {}".format(
                packet.framenumber, info.body_count
            )
        )

        if wanted_body is not None and wanted_body in body_index:
            # Extract one specific body
            wanted_index = body_index[wanted_body]
            position, rotation = bodies[wanted_index]
            print("{} - Pos: {}".format(wanted_body, position))
        else:
            # Print all bodies if wanted_body is not found by camera system
            for position, rotation in bodies:
                print("Pos: {} - Rot: {}".format(position, rotation))

    while True:
        # Start streaming frames
        await connection.stream_frames(components=["6d"], on_packet=on_packet)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream 6DoF data from QTM")
    parser.add_argument(
        "--file",
        metavar="PATH",
        help="Path to a .qtm file on the QTM server machine for file replay. Omit for real-time streaming.",
    )
    args = parser.parse_args()

    asyncio.run(main(qtm_file=args.file))
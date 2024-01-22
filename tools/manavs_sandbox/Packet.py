from dataclasses import dataclass


@dataclass
class Packet:
    timestamp: float
    name: str
    value: float

    # Takes in a raw packet from the log file and converts it into a Packet object
    # A raw packet is a list with 3 items: the type of packet (DAQ, CAN, etc.), the timestamp
    # in epoch format, and the payload of the packet
    # Note many packets contain a separate timestamp in their payload, this is ignored
    # Note many raw packets (Such as DAQ and CAN SensorAnalog) contain multiple Packets
    # inside, that is why this function will return a list of Packet objects
    @staticmethod
    def sort(raw_packet):
        packets = list()

        packet_type = raw_packet[0]
        timestamp = raw_packet[1]
        payload = raw_packet[2]

        # Parsley/Health packets contain only a board id and a
        # healthy/not-healthy status
        if packet_type == 'Parsley/Health':
            name = payload['id']
            value = payload['healthy']
            value = 100 if value == 'HEALTHY' else 0  # maps string value to 100 or 0
            packets.append(Packet(timestamp, name, value))

        # DAQ/Fake packets contain several channels, each channel
        # contains 200 values, this code just averages them into one.
        # Every channel is turned into its own Packet object
        elif packet_type == 'DAQ/Fake':
            payload = payload['data']
            for channel, data in payload.items():
                value = 0
                for val in data:
                    value += val
                value = value/len(data)
                packets.append(Packet(timestamp, channel, value))

        # CAN/Parsley packets are split into three known types obtained
        # from the 'msg_type' field:
        # General Board Status (giving the status of the entire PCB board),
        # ActuatorStatus (giving the value of an actuator connected to a board
        #       and also any requested values sent from ground control. These
        #       are split into two separate packets)
        # SensorStatus (giving the sensor readings from various sensors connected
        #       to each board)
        elif packet_type == 'CAN/Parsley':
            msg_type = payload['msg_type']

            if msg_type == 'GENERAL_BOARD_STATUS':
                name = payload['board_id']
                value = payload['data']['status']
                value = 100 if value == 'E_NOMINAL' else 0  # maps string value to 100 or 0
                packets.append(Packet(timestamp, name, value))

            elif msg_type == 'SENSOR_ANALOG':
                name = payload['data']['sensor_id']
                value = payload['data']['value']
                packets.append(Packet(timestamp, name, value))

            elif msg_type == 'ACTUATOR_STATUS':
                name1 = f"{payload['data']['actuator']} CURRENT"
                value1 = payload['data']['cur_state']
                value1 = 100 if value1 == 'ACTUATOR_ON' else 0  # maps string value to 100 or 0

                name2 = f"{payload['data']['actuator']} REQUESTED"
                value2 = payload['data']['req_state']
                value2 = 100 if value2 == 'ACTUATOR_ON' else 0  # maps string value to 100 or 0

                packets.append(Packet(timestamp, name1, value1))
                packets.append(Packet(timestamp, name2, value2))

        # An unknown packet type is received
        else:
            raise Exception(f'{packet_type} is an unknown data type (Code probably needs to be updated :p)')

        return packets

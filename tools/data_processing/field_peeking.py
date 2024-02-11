import argparse
import msgpack
import csv

messages = {}

def process_CAN_message(channel, payload):
    field_signature = {}
    # fill in the field signature for all the matches that we have in the format {"msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_VENT_VALVE"}
    if "board_id" in payload:
        field_signature["board_id"] = payload["board_id"]
    if "msg_type" in payload:
        field_signature["msg_type"] = payload["msg_type"]
    if "data" in payload:
        if "sensor_id" in payload["data"]:
            field_signature["data.sensor_id"] = payload["data"]["sensor_id"]
        if "actuator" in payload["data"]:
            field_signature["data.actuator"] = payload["data"]["actuator"]

    sig_text = str(field_signature)
    messages[(channel, payload.get("board_id", ""), payload.get("msg_type", ""), payload.get("data", {}).get("sensor_id", ""), payload.get("data", {}).get("actuator", ""),sig_text)] =  payload

def process_DAQ_message(channel, payload):
    for field in payload["data"]:
        messages[(channel,field)] = payload["data"][(field)][0]

def process_file(args, process_func, headers):
    with open(args.file, "rb") as infile:
        for full_data in msgpack.Unpacker(infile):
            channel, timestamp, payload = full_data
            if channel.startswith(args.channel):
                process_func(channel, payload)

    with open(f"unique_messages_{args.file.split('.log')[0]}_{args.channel}.csv", "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)
        for key, value in messages.items():
            row = [k for k in key] + [value]
            writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description="Read a messagepacked file and output all the unique messages to a text file")
    parser.add_argument("file", type=str, help="The file to read")
    parser.add_argument("channel", type=str, help="The channel to read")
    args = parser.parse_args()

    if args.channel.startswith("CAN"):
        process_file(args, process_CAN_message, ["channel","board_id", "msg_type", "sensor_id", "actuator","signature", "sample"])
    else:
        process_file(args, process_DAQ_message, ["channel", "field", "sample"])

if __name__ == "__main__":
    main()
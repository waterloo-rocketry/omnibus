# A quick script for Artem that dumps every message into a text

import msgpack
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Read a messagepacked file and output all the unique messages to a text file")
    parser.add_argument("file", type=str, help="The file to read")
    args = parser.parse_args()

    with open(args.file, "rb") as infile:
        with open(f"all_messages_{args.file.split('.log')[0]}.txt", "w") as outfile:
            for full_data in msgpack.Unpacker(infile):
                outfile.write(str(full_data) + "\n")


if __name__ == "__main__":
    main()

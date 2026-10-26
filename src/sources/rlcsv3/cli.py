import argparse

import autosequence


def non_negative_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid int value: {value!r}")
    if number < 0:
        raise argparse.ArgumentTypeError(f"must be >= 0, got {number}")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port to read from, or - for stdin')
    parser.add_argument('--solo', action='store_true',
                        help="Don't connect to omnibus - just print to stdout.")
    parser.add_argument('--auto-sequence', action='store_true',
                        help="DANGEROUS: open QD301 over USB without a manual command when "
                        "ignition is armed and held and the configured PT reaches its target "
                        "pressure. See autosequence.py for the constants.")
    parser.add_argument('--auto-sequence-time-ms', type=non_negative_int,
                        default=autosequence.AUTO_SEQUENCE_TIME_TO_FIRE_MS,
                        help="Override how long (ms) the conditions must hold before firing. "
                        "Default: %(default)s")
    args = parser.parse_args(argv)

    if args.auto_sequence and (args.solo or args.port == "-"):
        parser.error("--auto-sequence needs Omnibus and a real serial port "
                     "(not --solo or port -)")
    if (not args.auto_sequence
            and args.auto_sequence_time_ms != autosequence.AUTO_SEQUENCE_TIME_TO_FIRE_MS):
        parser.error("--auto-sequence-time-ms requires --auto-sequence")
    return args

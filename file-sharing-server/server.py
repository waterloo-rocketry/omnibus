import os
import sys
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

def check_permissions(folder):
    # check if user has READ access
    if os.access(folder, os.R_OK):
        return True
    else:
        return False

def start_ftp_server(folder):
    authorizer = DummyAuthorizer()

    # add user with only read permissions
    authorizer.add_anonymous(folder)

    handler = FTPHandler
    handler.authorizer = authorizer

    address = ("0.0.0.0", 21)

    # run server
    try: 
        server = FTPServer(address, handler)
    except:
        print("Insufficient permissions for running FTP server => Try running as root.")
        sys.exit(1)

    print(f"Starting FTP server at {folder}")
    server.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ftp_server.py <folder>")
        sys.exit(1)

    folder = sys.argv[1]

    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid directory.")
        sys.exit(1)

    if not check_permissions(folder):
        print(f"Error: Insufficient permissions for folder {folder}.")
        sys.exit(1)

    start_ftp_server(folder)

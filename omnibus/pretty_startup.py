## Pretty Startup - Print version information (and cool ASCII) on startup ##
# This is not runtime essential, so its been split into a separate file #
from datetime import datetime, timezone


def run_startup_screen():
    short_hash = "UNKNOWN"
    date = "N/A"
    try:
        import git
        repo = git.Repo(search_parent_directories=True)
        hash = repo.head.object.hexsha
        date = repo.head.commit.committed_datetime.strftime(rf'%Y-%m-%d %H:%M%:%S')
        short_hash = repo.git.rev_parse(hash, short=7)
        repo.close()
    except ImportError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M%:%S')}] [INFO] GitPython is not installed, unable to get version info!")
    print(rf"""
 __        ___  _____ _____ ____  _     ___   ___  
 \ \      / / \|_   _| ____|  _ \| |   / _ \ / _ \ 
  \ \ /\ / / _ \ | | |  _| | |_) | |  | | | | | | |
   \ V  V / ___ \| | | |___|  _ <| |__| |_| | |_| |
    \_/\_/_/ _ \_\_|_|_____|_|_\_\_____\___/_\___/ 
   |  _ \ / _ \ / ___| |/ / ____|_   _|  _ \ \ / / 
   | |_) | | | | |   | ' /|  _|   | | | |_) \ V /  
   |  _ <| |_| | |___| . \| |___  | | |  _ < | |   
   |_| \_\\___/ \____|_|\_\_____| |_| |_| \_\|_|   
                                                   """)
    print(f"{'=' * 52}\nOmnibus - build {short_hash} from {date}\n{'=' * 52}\n")

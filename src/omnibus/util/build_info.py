from datetime import datetime

WATERLOO_ROCKETRY_ASCII_STR = rf"""
 __        ___  _____ _____ ____  _     ___   ___  
 \ \      / / \|_   _| ____|  _ \| |   / _ \ / _ \ 
  \ \ /\ / / _ \ | | |  _| | |_) | |  | | | | | | |
   \ V  V / ___ \| | | |___|  _ <| |__| |_| | |_| |
    \_/\_/_/ _ \_\_|_|_____|_|_\_\_____\___/_\___/ 
   |  _ \ / _ \ / ___| |/ / ____|_   _|  _ \ \ / / 
   | |_) | | | | |   | ' /|  _|   | | | |_) \ V /  
   |  _ <| |_| | |___| . \| |___  | | |  _ < | |   
   |_| \_\\___/ \____|_|\_\_____| |_| |_| \_\|_|   
                                                   """


class BuildInfoManager:
    """
    Class to get and print the build version of the currently installed
    Omnibus instance using GitPython and the information encoded within
    the Omnibus Git repository.

    The build_number is defined as the 7 character commit hash from the
    HEAD of the repo, to match GitHub's format. The build_date is the date
    of that commit.

    Handles failure if a git repo is not found.

    Requires: Omnibus must be installed through the git tree, GitPython must be installed.
    """

    build_number: str  # defaults to UNKNOWN if not found
    build_date: str  # defaults to N/A if no build information is available
    app_name: str | None

    _full_commit_hash: str

    def __init__(self, app_name: str | None = None):
        self.app_name = app_name
        try:
            import git  # Import here to prevent the version check from holding up the application

            repo = git.Repo(search_parent_directories=True)
            self._full_commit_hash = str(repo.head.object.hexsha)
            self.build_date = repo.head.commit.committed_datetime.strftime(
                "%Y-%m-%d %H:%M:%S %z"
            )
            self.build_number = self._full_commit_hash[:7]
            repo.close()
            return
        except ImportError:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] BuildInfoManager: GitPython is not installed, unable to get version info!"
            )
        except:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] BuildInfoManager: Failed to get version info!"
            )
        self.build_number = "UNKNOWN"
        self._full_commit_hash = "UNKNOWN"
        self.build_date = "N/A"

    def print_startup_screen(self):
        """
        Prints a startup screen, including Waterloo Rocketry ASCII art, as well as the build number and
        date.
        """
        print(WATERLOO_ROCKETRY_ASCII_STR)
        print(
            f"{'=' * 54}\nOmnibus - build {self.build_number} from {self.build_date}\n{'=' * 54}\n"
        )

    def print_app_name(self):
        """
        Formatted print of the name of the source/sink/module, if provided at initialization.
        If not, simply returns nothing silently.
        """
        if not self.app_name:
            return
        print(f"{'=' * 10} {self.app_name} {'=' * 10}")

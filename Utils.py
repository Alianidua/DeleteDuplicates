class bcolors:
    OK = '\033[1m\033[96m'       # Cyan
    WARN = '\033[1m\033[93m'      # Yellow
    ERROR = '\033[1m\033[91m'    # Red
    INFO = '\033[1m\033[94m'     # Blue
    RESET = '\033[1m\033[0m'     # White
    SUCCESS = '\033[1m\033[92m'  # Light green

color_map = {
    "OK": bcolors.OK,
    "WARN": bcolors.WARN,
    "ERROR": bcolors.ERROR,
    "INFO": bcolors.INFO,
    "SUCCESS": bcolors.SUCCESS
}

def logs(*args, level="INFO", **kwargs):
    color = color_map.get(level, bcolors.INFO)
    level += max(5 - len(level), 0) * " "
    print(f"[{color}{level}{bcolors.RESET}]", *args, bcolors.RESET, **kwargs)

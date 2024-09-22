class Colors:
    RED = '\033[91m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'

def printInfo(text):
    print(Colors.WHITE + "[INFO] " + text + Colors.RESET)

def printWarn(text):
    print(Colors.YELLOW + "[WARN] " + text + Colors.RESET)

def printError(text):
    print(Colors.RED + "[ERROR] " + text + Colors.RESET)

def printDebug(text):
    print(Colors.BLUE + "[DEBUG] " + text + Colors.RESET)
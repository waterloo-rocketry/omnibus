import requests

def check_internet(url='http://www.google.com/', timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        return True
    except (requests.ConnectionError, requests.Timeout):
        return False

if __name__ == "__main__":
    if check_internet():
        print("Internet connection is available.")
    else:
        print("No internet connection.")
import bme280
import sys
import time
from datetime import datetime
import requests

max_try = 300
slack_url = None
csv_path = None


# time , temperature , humidity , cpu_temp, pressure
def print_csv(temperature, humidity, cpu_temp, pressure):
    t = time.time()
    now = datetime.fromtimestamp(t)
    if temperature == 0 and humidity == 0 and pressure == 0:
        # Failed to get values.
        print(f"{now} , , , {cpu_temp}, ")
    else:
        print(f"{now} , {temperature:-6.2f} ,{humidity:6.2f} , {cpu_temp}, {pressure:7.2f}")


def get_cpu_temp():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        result = int(f.readline())
        return result / 1000


def send_to_slack(text):
    global slack_url
    if slack_url is not None:
        resp = requests.post(slack_url,
                             data={"payload": {"text": text}.__str__()})
        return resp.status_code == 200
    return True


def is_last_success():
    global csv_path
    with open(csv_path, "r") as f:
        data = f.readlines()
        return data[len(data) - 1].find(f", , ,") == -1


def main():
    try:
        i = 0
        for i in range(max_try + 1):
            pressure, temperature, humidity = bme280.readData()
            cpu_temp = get_cpu_temp()
            if pressure == 0 and temperature == 0 and humidity == 0:
                # wait 5 seconds and retry if failed.
                time.sleep(5)
                continue
            if not is_last_success():
                send_to_slack("Recovered from failure")
            print_csv(temperature, humidity, cpu_temp, pressure)
            return
        cpu_temp = get_cpu_temp()
        # Failed to get data.
        if is_last_success():
            send_to_slack("Failed to get data from BME280")
        print_csv(0, 0, cpu_temp, 0)
    except:
        pass


def usage():
    print("python3 main.py [csv path] [slack webhook url]")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "-h":
            usage()
        csv_path = sys.argv[1]
    if len(sys.argv) > 2:
        slack_url = sys.argv[2]

    main()

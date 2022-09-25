import random
import string
import time
from adb_shell.adb_device import AdbDeviceTcp
import subprocess
from ppadb.client import Client as AdbClient
import time
from adb_shell.adb_device import AdbDeviceTcp
import subprocess
from ppadb.client import Client as AdbClient


def collect_ids(device):
    # read current gaid
    try:
        current_gaid_raw = device.shell(
            'grep adid_key /data/data/com.google.android.gms/shared_prefs/adid_settings.xml')
        current_gaid = current_gaid_raw.split('<string name="adid_key">')[1].split('</string>')[0]
        print(current_gaid)
    except:
        print('gaid not yet obtained after deleting file')


def find_device():
    adb_path = r'c:\Program Files\Nox\bin\adb.exe'
    list_of_devices = subprocess.run([adb_path, 'devices'],
                                     capture_output=True,
                                     encoding="utf-8")

    # parse device ip:port
    try:
        device_in_list = list_of_devices.stdout.splitlines()[1]
        device_ip = device_in_list.split(':')[0]
        device_port = int(device_in_list.split(':')[1].split('\t')[0])
        print(f'try to connect a device on {device_ip}:{device_port}')
        return device_ip, device_port
    except:
        return print('0 devices found')


def connect_device(device_ip: str, device_port: int):
    # connect to device
    try:
        device = AdbDeviceTcp(device_ip, device_port, default_transport_timeout_s=9.)
        device.connect()
        print('device connected')
        return device
    except:
        print('cant connect device')
        return False


def install_app(ip: str, port: int, apk_path:str):
    client = AdbClient(host="127.0.0.1", port=5037)  # host machine
    # devices = client.devices()
    # device = client.device("127.0.0.1:62033")
    device = client.device(f'{ip}:{port}')
    device.install(apk_path)


def save_result():
    with open('results.txt', mode='r', encoding='utf-8') as file:
        install_count = int(file.readline().split(':')[1])
        install_count += 1
    with open('results.txt', mode='w', encoding='utf-8') as file:
        file.writelines(f'install_count:{install_count}')


def get_active_window(device):
    try:
        # print(device.shell('dumpsys window windows | grep mCurrentFocus'))
        # print(active_window_package_name)
        return device.shell('dumpsys window windows | grep mCurrentFocus').split(' ')[4]
    except:
        print('fail: getting active window')
        return ''


def gen_new_device():
    noxexe_path = r'C:\Program Files\Nox\bin\Nox.exe'
    clone = f'Nox_{15}'
    manufacturer = 'google'
    model = 'SM-G973N'
    # imei = '098765432112345'
    imei = ''.join(random.choices(string.digits, k=15))
    print(imei)
    params = f' -clone:{clone} -manufacturer:{manufacturer} -model:{model} -imei:{imei}'
    run_cmd = f'{noxexe_path}{params}'
    launch_cmd = subprocess.run(run_cmd,
                                capture_output=True,
                                encoding="utf-8")

    print('hi')
    # time.sleep(90)
    # quit_cmd = f'{noxexe_path} -clone:{clone} -quit'


def main():
    gen_new_device()
    time.sleep(40)

    # find device
    device_ip, device_host = find_device()

    # connect device
    device = connect_device(device_ip, device_host)

    # reset gaid by deleting its carrier file
    device.shell('rm -f /data/data/com.google.android.gms/shared_prefs/adid_settings.xml')
    # clear gsf id
    device.shell('pm clear com.google.android.gsf')
    # takes a while to open google settings after command below
    device.shell('pm clear com.google.android.gms')

    browser_app = 'com.android.browser'   # package name
    device.shell('pm clear com.android.browser')
    device.shell(f'am start -a android.intent.action.VIEW -d "my user agent" {browser_app}')


if __name__ == '__main__':
    # track program execution time
    start_ts = time.time()
    print(f'start time: {time.strftime("%I:%M:%S %p")}')
    main()
    print(f'finish time: {time.strftime("%I:%M:%S %p")}')
    print(f'execution time: {time.time() - start_ts}')

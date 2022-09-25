import random
import time
from adb_shell.adb_device import AdbDeviceTcp
import subprocess
from ppadb.client import Client as AdbClient


# not used yet
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


def main_action():
    # find device
    device_ip, device_host = find_device()

    # connect device
    device = connect_device(device_ip, device_host)

    # variables to adjust
    app_name = 'ru.letu'    # package name
    url1 = 'https://getb.pl/2ctjY'
    # browser_app = 'com.android.browser'   # package name
    browser_app = 'com.kiwibrowser.browser'  # package name
    # apk_path = 'letu_v1.22.0_apkpure.com.apk'   # android5
    apk_path = 'letu_v1.48.1_apkpure.com.apk'   # android9

    # make sure apps are closed
    device.shell(f'am force-stop {app_name}')
    device.shell(f'am force-stop {browser_app}')

    # unistall app
    device.shell(f'pm uninstall {app_name}')

    # reset gaid by deleting its carrier file
    device.shell('rm -f /data/data/com.google.android.gms/shared_prefs/adid_settings.xml')
    # clear gsf id
    device.shell('pm clear com.google.android.gsf')
    # takes a while to open google settings after command below
    device.shell('pm clear com.google.android.gms')
    time.sleep(3)

    # # start playstore app just in case all ids received
    # device.shell('monkey -p com.android.vending 1')

    # open browser and go to url
    device.shell(f'am start -a android.intent.action.VIEW -d "{url1}" {browser_app}')
    time.sleep(15)

    # get active window
    active_window_package_name = get_active_window(device)

    # sometimes redirect to playstore doesn't happen
    # and it takes 20s for confirmation window to appear
    if browser_app in active_window_package_name:
        time.sleep(21)
        # x824 y240 coordinates of in-browser button allowing redirect to playstore
        device.shell(f'input tap 824 240')
        time.sleep(5)

        # stop if reflink time out
        active_window_package_name = get_active_window(device)
        if browser_app in active_window_package_name:
            print('reflink connection time out. Process stopped')
            return False

    # play store package name
    # mCurrentFocus=Window{5f2d027 u0 com.android.vending/com.google.android.finsky.activities.MainActivity}
    if 'com.android.vending' in active_window_package_name:
        print('reflink go successful. Playstore opened')

    # if reflink go happened continue install
    print(f'starting install {apk_path}')
    install_app(device_ip, device_host, apk_path)
    sleep_time = 20
    print(f'sleeping {sleep_time}s after install before launch')
    time.sleep(sleep_time)
    device.shell(f'monkey -p {app_name} 1')

    # save counter
    save_result()
    time.sleep(10)

    # close app
    device.shell(f'am force-stop {app_name}')

    # # minimize all windows
    # device.shell('input keyevent KEYCODE_HOME')

    return True


def main():
    gos_period = True
    # gos_period = False
    number_of_gos = 4
    pause_min = 40
    pause_max = 310
    action_cnt = 0  # successful installs

    for n in range(number_of_gos):

        if main_action():
            action_cnt += 1
            print(f'...\n{action_cnt} installs done')

        if gos_period and action_cnt != number_of_gos:
            pause_time = random.randint(pause_min, pause_max)  # in seconds
            print(f'sleeping for {pause_time}s before next cycle\n...')
            time.sleep(pause_time)


def print_info(device):
    # print installed apps
    # system apps
    print(device.shell('cd /system/app && ls'))
    # user apps
    print(device.shell('pm list packages -3'))
    # list everything
    print(device.shell('pm list packages -f'))
    # download folder
    print(device.shell('cd /storage/emulated/0/Download && ls'))
    pass


if __name__ == '__main__':
    # track program execution time
    start_ts = time.time()
    print(f'start time: {time.strftime("%I:%M:%S %p")}')
    main()
    print(f'finish time: {time.strftime("%I:%M:%S %p")}')
    print(f'execution time: {time.time() - start_ts}')

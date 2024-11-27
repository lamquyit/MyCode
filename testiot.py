import minimalmodbus
import json
import requests
import time


def read_refresh_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def write_refresh_token(file_path, token):
    with open(file_path, 'w') as file:
        json.dump(token, file)


def is_token_valid(token_infor):
    current_time = time.time()
    expiration_time = int(
        token_infor['expires_in']) + int(token_infor['token_obtained_at'])
    return current_time < expiration_time


def check_and_update_access_token(token_infor, app_id, app_secret):
    if not is_token_valid(token_infor):
        print("Access token đã hết hạn. Đang lấy access token mới...")
        new_token_infor = get_access_token(
            token_infor['refresh_token'], app_id, app_secret)
        if new_token_infor:
            if 'access_token' in new_token_infor and 'refresh_token' in new_token_infor and 'expires_in' in new_token_infor:
                token_infor['access_token'] = new_token_infor['access_token']
                token_infor['refresh_token'] = new_token_infor['refresh_token']
                token_infor['expires_in'] = new_token_infor['expires_in']
                token_infor['token_obtained_at'] = time.time()
                write_refresh_token(refresh_token_file, token_infor)
            return new_token_infor['access_token']
    else:
        return token_infor['access_token']


# lấy access_token và data_token


def get_access_token(refresh_token, app_id, client_secret):
    token_url = "https://oauth.zaloapp.com/v4/oa/access_token"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'secret_key': client_secret
    }
    payload = {
        'refresh_token': refresh_token,
        'app_id': app_id,
        'grant_type': 'refresh_token'
    }

    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code == 200:
        try:
            token_infor = response.json()
            # In ra phản hồi JSON để kiểm tra chi tiết
            print("Phản hồi JSON:", token_infor)
            return token_infor
        except requests.exceptions.JSONDecodeError:
            print("Phản hồi từ máy chủ không phải là JSON hợp lệ.")
            print("Phản hồi:", response.text)
            return None
    else:
        print("Lỗi khi lấy access token:", response.status_code, response.text)
        return None


# def template_data():
#     # now = datetime.now()
#     unixTime = int(time.time() * 1000)
#     headers = {
#         'Content-Type': 'application/json',
#         'Accept': 'application/json'
#     }

#     data = {
#         'username': 'tenant.fuji@at-energy.vn',
#         'password': 'atenergy'
#     }

#     login_url = 'https://iot.at-energy.vn/api/auth/login'
#     response = requests.post(
#         login_url, headers=headers, json=data, verify=False)
#     response.raise_for_status()

#     token = response.json().get('token')

#     if token:

#         deviceID = '322754c0-2e04-11ef-8b78-d57bff4cf0f1'

#         data = float(get_data(deviceID, keys, token))

#         return data


# sau khi lấy được access token sẽ gửi request(phải lấy data từ iot trước)


def request_ZNS(access_token, data_KWH):
    url = "https://business.openapi.zalo.me/message/template"
    phone = "84982872942"
    request_data = {
        "phone": phone,
        "template_id": "387718",
        "template_data": {
            "address": "Văn Phòng",
            "temperature": data_KWH,
            "humidity": 0,
            "status": "RED",
        },
    }

    headers = {
        "Content-Type": "application/json",
        "access_token": access_token
    }

    response = requests.post(url, json=request_data, headers=headers)

    print(response.json())


app_id = "41245079024148581"
app_secret = "PHO0H61G5v58NRXKR465"
refresh_token_file = r"/home/maxicom/Documents/refresh_token.json"

all_token = read_refresh_file(refresh_token_file)
access_token = check_and_update_access_token(all_token, app_id, app_secret)

count = 0
max_runs = 1


def run(access_token, data_KWH):
    global count
    count += 1
    print(f"Chạy lần thứ {count}")
    if access_token:
        request_ZNS(access_token, data_KWH)
    else:
        print("lỗi access_token")
    if count >= max_runs:
        print("Đã hoàn thành số lần chạy yêu cầu.")


# Cấu hình thiết bị Modbus
# '/dev/ttyUSB0': cổng RS-485, ID Modbus là 1
instrument = minimalmodbus.Instrument('/dev/ttyUSB0', slaveaddress=1)
instrument.serial.baudrate = 9600  # Baudrate (tùy theo cảm biến)
instrument.serial.bytesize = 8
instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout = 1

while True:
    try:

        temperature = instrument.read_register(
            0x0003, 1)  # 1 là số chữ số thập phân
        print(f"Nhiệt độ: {temperature}°C")

        access_token2 = 'abTeGKm38w67AKr5nwSi'
        url = f'https://iot.at-energy.vn/api/v1/{access_token2}/telemetry'

        # Dữ liệu JSON bạn muốn gửi
        data = {
            "temperature": temperature
        }

        # Headers để xác định kiểu dữ liệu là JSON
        headers = {
            "Content-Type": "application/json"
        }
        # Gửi yêu cầu POST
        response = requests.post(url, json=data, headers=headers, verify=False)
        if temperature > 50:
            run(access_token=access_token,
                data_KWH=temperature)
            print('đã gửi tin nhắn Cảnh báo')
        # In ra kết quả phản hồi
        if response.status_code == 200:
            print("Yêu cầu thành công!")
        else:
            print(f"Yêu cầu thất bại với mã lỗi {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Lỗi: {e}")

    time.sleep(2)

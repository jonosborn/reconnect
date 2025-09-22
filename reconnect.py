#!/usr/bin/env python3
import subprocess
import time
import sys
import logging
import os

# Настройка логирования
logging.basicConfig(
    filename='./wifi-reconnect.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_password_from_pass(pass_dir):
    try:
        # Получаем пароль из хранилища pass
        password = subprocess.run(
            ['pass', 'show', pass_dir],
            capture_output=True,
            text=True,
            check=True
        )
        return password.stdout.strip()
    except Exception as e:
        logging.error(f"Ошибка при получении пароля: {e}")
        return None

def check_ethernet_connection():
    try:
        # Проверяем наличие активных Ethernet-интерфейсов
        result = subprocess.run(
            ['ip', '', 'status'],
            capture_output=True,
            text=True
        )
        for line in result.stdout.splitlines():
            if 'ethernet' in line.lower() and 'connected' in line.lower():
                return True
        return False
    except Exception as e:
        logging.error(f"Ошибка при проверке Ethernet: {e}")
        return False

def check_wifi_status(interface):
    try:
        result = subprocess.run(
            ['iwctl', 'station', interface, 'show'],
            capture_output=True,
            text=True
        )
        # Ищем строку с состоянием
        for line in result.stdout.splitlines():
            if 'State' in line:
                state = line.split()[1].strip()
                return state.lower() == 'connected'
        return False
    except Exception as e:
        logging.error(f"Ошибка при проверке статуса: {e}")
        return False

def reconnect_wifi(interface, ssid, password):
    try:
        connect = ['iwctl', 'station', interface, 'connect', ssid]
        if password:
            connect.insert(3, '--passphrase')
            connect.insert(4, password)
            
        logging.info(f"Попытка подключения к сети {ssid}")
        subprocess.run(connect, check=True)
        time.sleep(5)  # Ждем подключения
    except Exception as e:
        filtred_msg = str(e).replace(password, "****") if password else str(e)
        logging.error(f"Ошибка при переподключении: {filtred_msg}")

def main():
    INTERFACE = os.environ.get('WIFI_INTERFACE', 'wlx')
    pass_dir = os.environ.get('PASS_DIR', 'wifi')  # Файл содержит только пароль
    WIFI_SSID = os.environ.get('WIFI_SSID', 'NerVV')  # SSID теперь хранится в переменной окружения
    
    # Проверяем наличие Ethernet-подключения
    if check_ethernet_connection():
        logging.info("Обнаружено активное Ethernet-подключение, выход из скрипта")
        sys.exit(0)
    
    if not check_wifi_status(INTERFACE):
        logging.info("Wi-Fi не подключен, попытка переподключения...")
        
        ssid = WIFI_SSID
        password = get_password_from_pass(pass_dir)
        
        if not ssid:
            logging.error("Не удалось получить SSID сети")
            sys.exit(1)
        
        logging.info(f"Получен SSID: {ssid}")
        
        if not password:
            logging.warning("Пароль не найден, будет попытка подключения без пароля")
        
        reconnect_wifi(INTERFACE, ssid, password)
        
        if check_wifi_status(INTERFACE):
            logging.info("Подключение успешно восстановлено")
        else:
            logging.error("Не удалось восстановить подключение")
            sys.exit(1)

if __name__ == "__main__":
    main()

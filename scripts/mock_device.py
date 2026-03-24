import os
import random
import time
from datetime import datetime, timezone

import requests


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
DEVICE_UID = os.getenv("DEVICE_UID", "ESP32-C3-001")
DEVICE_KEY = os.getenv("DEVICE_KEY")
INTERVAL = float(os.getenv("INTERVAL", "1.0"))


def build_payload() -> dict:
    return {
        "device_uid": DEVICE_UID,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "gsr": round(random.uniform(0.2, 1.2), 3),
        "heart_rate": random.randint(70, 110),
        "temperature": round(random.uniform(36.2, 37.8), 2),
        "blood_pressure_sys": random.randint(95, 125),
        "blood_pressure_dia": random.randint(60, 85),
        "battery_level": random.randint(50, 100),
    }


def main() -> None:
    headers = {}
    if DEVICE_KEY:
        headers["X-DEVICE-KEY"] = DEVICE_KEY

    while True:
        payload = build_payload()
        response = requests.post(
            f"{BASE_URL}/api/sensor-data", json=payload, headers=headers, timeout=10
        )
        print("payload:", payload)
        print("response:", response.status_code, response.text)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()

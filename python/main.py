from __future__ import annotations

import hashlib
import json
import unittest

import requests
from bs4 import BeautifulSoup

session = requests.Session()

TIMEOUT = 5


def combine_date_time(
    tracking_data: list[dict[str, str]],
    date_key: str,
    time_key: str,
) -> list[dict[str, str]]:
    for step in tracking_data:
        if date_key in step and time_key in step:
            step["combined_time"] = f"{step[date_key]} {step[time_key]}"
    return tracking_data


def generate_unique_id(*args: str) -> str:
    combined_string = " ".join(str(arg) for arg in args)
    return hashlib.sha256(combined_string.encode("utf-8")).hexdigest()


def parse_tracking_data(
    tracking_data: list[dict[str, str]],
    key_mappings: dict[str, str],
    reverse_order: bool,  # noqa: FBT001
) -> dict[str, dict[str, str]]:
    tracking_info = {}
    steps = reversed(tracking_data) if reverse_order else tracking_data
    for step in steps:
        time_message = step.get(key_mappings.get("time", ""), "N/A")
        tracking_message = step.get(key_mappings.get("message", ""), "N/A")
        location_message = step.get(key_mappings.get("location", ""), "N/A")
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
            "location": location_message,
        }
    return tracking_info


def track_acs(tracking_number: str) -> dict[str, dict[str, str]]:
    base_url = "https://www.acscourier.net/"
    base_response = session.get(base_url, timeout=TIMEOUT)
    soup = BeautifulSoup(base_response.text, "html.parser")
    app_root = soup.find(id="app-root")
    public_token = app_root.get("publictoken")
    url = f"https://api.acscourier.net/api/parcels/search/{tracking_number}"
    headers = {
        "X-Encrypted-Key": public_token,
        "Origin": base_url,
    }
    response = session.get(url, headers=headers, timeout=TIMEOUT)
    tracking_data = response.json()["items"][0]["statusHistory"]
    return parse_tracking_data(
        tracking_data,
        {"time": "controlPointDate", "message": "controlPoint"},
        reverse_order=True,
    )


def track_boxnow(tracking_number: str) -> dict[str, dict[str, str]]:
    url = "https://api-production.boxnow.gr/api/v1/parcels:track"
    json_data = {"parcelId": tracking_number}
    response = session.post(url, json=json_data, timeout=TIMEOUT)
    tracking_data = response.json()["data"][0]["events"]
    return parse_tracking_data(
        tracking_data,
        {"time": "createTime", "message": "type", "location": "locationDisplayName"},
        reverse_order=True,
    )


def track_cainiao(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://global.cainiao.com/global/detail.json?mailNos={tracking_number}"
    response = session.get(url, timeout=TIMEOUT)
    tracking_data = response.json()["module"][0]["detailList"]
    return parse_tracking_data(
        tracking_data,
        {"time": "timeStr", "message": "desc", "location": "standerdDesc"},
        reverse_order=False,
    )


def track_easymail(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://trackntrace.easymail.gr/{tracking_number}"
    response = session.get(url, timeout=TIMEOUT)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    table_element = soup.find("div", class_="col mobiRemoveMargin")
    tbody_element = table_element.find("tbody")
    tracking_data = tbody_element.find_all("tr")
    tracking_info = {}
    for step in tracking_data:
        columns = step.find_all("td")
        time_message = columns[0].text.strip()
        tracking_message = columns[1].text.strip()
        location_message = columns[2].text.strip()
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
            "location": location_message,
        }
    return tracking_info


def track_elta(tracking_number: str) -> dict[str, dict[str, str]]:
    url = "https://www.elta.gr/trackApi"
    payload = {"code[]": tracking_number, "in_lang": "1"}
    response = session.post(url, data=payload, timeout=TIMEOUT)
    tracking_data = response.json()[0]["response"]["out_status"]
    tracking_data = combine_date_time(tracking_data, "out_date", "out_time")
    return parse_tracking_data(
        tracking_data,
        {
            "time": "combined_time",
            "message": "out_status_name",
            "location": "out_station",
        },
        reverse_order=False,
    )


def track_eltac(tracking_number: str) -> dict[str, dict[str, str]]:
    url = "https://www.elta-courier.gr/track.php"
    payload = {"number": tracking_number}
    response = session.post(url, data=payload, timeout=TIMEOUT)
    response_data = json.loads(response.content.decode("utf-8-sig"))
    tracking_data = response_data["result"][tracking_number]["result"]
    tracking_data = combine_date_time(tracking_data, "date", "time")
    return parse_tracking_data(
        tracking_data,
        {"time": "combined_time", "message": "status", "location": "place"},
        reverse_order=False,
    )


def track_eshop(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://www.e-shop.gr/status.phtml?id={tracking_number}"
    response = session.get(url, timeout=TIMEOUT)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    td_element = soup.find(
        "td",
        style=(
            "font-family:tahoma;font-size:14px;color:4a4a4a;"
            "font-weight:bold;border-bottom:2px #ffcc00 solid;"
            "padding:3px 0 5px 0;"
        ),
    )
    table_element = td_element.parent.parent
    tracking_data = table_element.find_all("tr")
    tracking_info = {}
    for step in reversed(tracking_data):
        columns = step.find_all("td")
        status_icon = columns[0].find("img")
        if status_icon and "check_ok.png" in status_icon["src"]:
            time_message = columns[2].text.strip()
            tracking_message = columns[1].text.strip()
            unique_id = generate_unique_id(time_message, tracking_message)
            tracking_info[unique_id] = {
                "time": time_message,
                "message": tracking_message,
            }
    return tracking_info


def track_geniki(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://www.taxydromiki.com/en/track/{tracking_number}"
    response = session.get(url, timeout=TIMEOUT)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    tracking_data = soup.find_all("div", class_="tracking-checkpoint")
    tracking_info = {}
    for step in reversed(tracking_data):
        tracking_message = (
            step.find("div", class_="checkpoint-status")
            .text.replace("Status", "")
            .strip()
        )
        location_div = step.find("div", class_="checkpoint-location")
        location_message = (
            location_div.text.replace("Location", "").strip() if location_div else "N/A"
        )
        date = (
            step.find("div", class_="checkpoint-date").text.replace("Date", "").strip()
        )
        time = (
            step.find("div", class_="checkpoint-time").text.replace("Time", "").strip()
        )
        time_message = f"{date} {time}"
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
            "location": location_message,
        }
    return tracking_info


def track_plaisio(tracking_number: str) -> dict[str, dict[str, str]]:
    url = "https://www.plaisio.gr/mercury/plaisio/ordertracking/getordertracking"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"
        ),
    }
    json_data = {
        "TrackingNumber": tracking_number,
    }
    response = session.post(url, headers=headers, json=json_data, timeout=TIMEOUT)
    tracking_data = response.json()["orderHistory"]
    return parse_tracking_data(
        tracking_data,
        {"time": "transactionDate", "message": "statusDescription"},
        reverse_order=True,
    )


def track_skroutz(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://api.sendx.gr/user/hp/{tracking_number}"
    response = session.get(url, timeout=TIMEOUT)
    tracking_data = response.json()["trackingDetails"]
    return parse_tracking_data(
        tracking_data,
        {"time": "updatedAt", "message": "description"},
        reverse_order=False,
    )


def track_sunyou(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://www.sypost.net/queryTrack?trackNumber={tracking_number}&toLanguage=en_US"
    response = session.get(url, timeout=TIMEOUT)
    jsonp_content = response.text
    start_index = jsonp_content.index("(") + 1
    end_index = jsonp_content.rindex(")")
    json_str = jsonp_content[start_index:end_index]
    tracking_data = json.loads(json_str)["data"][0]["result"]["origin"]["items"]
    return parse_tracking_data(
        tracking_data,
        {"time": "createTime", "message": "content"},
        reverse_order=False,
    )


class TestTracking(unittest.TestCase):
    def test_acs(self: TestTracking) -> None:
        tracking_info = track_acs("3482598254")
        correct_hash = (
            "80636753554fcfe07f9bf943f61f93035d63514c0213d13d8a39740eb4ae75da"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_boxnow(self: TestTracking) -> None:
        tracking_info = track_boxnow("9232100105")
        correct_hash = (
            "4ed9fdf53544b92c720366646e8f5bd061c88c52dc5e3ad21fa223a6d4a6b4fb"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_cainiao(self: TestTracking) -> None:
        tracking_info = track_cainiao("7605228735")
        correct_hash = (
            "75833d19fcadaf33ae5584efcf80d1846c178fc8633e672c78fcff9743c80968"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_easymail(self: TestTracking) -> None:
        tracking_info = track_easymail("013638451354")
        correct_hash = (
            "89d00851062b1066ca4347084c87cac4c375d6b915deea25c1caf4964b388ef2"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_elta(self: TestTracking) -> None:
        tracking_info = track_elta("LA114239535GB")
        correct_hash = (
            "93962002d8413f7e9895b791252a84556beb13f2c048986390c46c388a84eab2"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_eltac(self: TestTracking) -> None:
        tracking_info = track_eltac("LA114239535GB")
        correct_hash = (
            "6fb3264e2282e2e250e8c2193509a4d73ee0fdd9faf044b0fc378dcab5c00adb"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_eshop(self: TestTracking) -> None:
        tracking_info = track_eshop("1811032036589467232221")
        correct_hash = (
            "f77c7199dd1bf9e414d6e82e63a19f8c7a7e64f5f1ea75ec195e90c944b4e28f"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_geniki(self: TestTracking) -> None:
        tracking_info = track_geniki("3951159041")
        correct_hash = (
            "4efb2456419450175f91bf7a64d06057603819de869bd73617da3332cecaa676"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_plaisio(self: TestTracking) -> None:
        tracking_info = track_plaisio("5125957")
        correct_hash = (
            "779c9b4b1ee8f7d086f2c7f1005467a6f483afd1af64a2b1e88bd845f3370079"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_skroutz(self: TestTracking) -> None:
        tracking_info = track_skroutz("JLD6ZN7P8YD4W")
        correct_hash = (
            "47cd388c51186d7aac4803ab6e8818d9adbaca7a90d541fa53e09a69672ee767"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_sunyou(self: TestTracking) -> None:
        tracking_info = track_sunyou("SYAE006809461")
        correct_hash = (
            "60060cef334d81243bb1981b9c5e02f638e490072d068762541775f0d0e5f2d9"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError


def parcel_tracker(tracking_number: str, shipping: str) -> dict[str, dict[str, str]]:
    tracking_functions = {
        "acs": track_acs,
        "boxnow": track_boxnow,
        "cainiao": track_cainiao,
        "easymail": track_easymail,
        "elta": track_elta,
        "eltac": track_eltac,
        "eshop": track_eshop,
        "geniki": track_geniki,
        "plaisio": track_plaisio,
        "skroutz": track_skroutz,
        "sunyou": track_sunyou,
    }
    track_func = tracking_functions.get(shipping)
    if not track_func:
        msg = f"Unsupported shipping service: {shipping}"
        raise ValueError(msg)
    return track_func(tracking_number)


def main() -> None:
    import fire

    fire.Fire(parcel_tracker)


if __name__ == "__main__":
    unittest.main()

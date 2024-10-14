from __future__ import annotations

import datetime
import hashlib
import json
import unittest

import requests
from bs4 import BeautifulSoup


def generate_unique_id(*args: str) -> str:
    combined_string = " ".join(args)
    return hashlib.sha256(combined_string.encode("utf-8")).hexdigest()


def track_acs(tracking_number: str) -> dict[str, dict[str, str]]:
    base_url = "https://www.acscourier.net/"
    base_response = requests.get(base_url, timeout=5)
    soup = BeautifulSoup(base_response.text, "html.parser")
    app_root = soup.find(id="app-root")
    public_token = app_root.get("publictoken")
    url = f"https://api.acscourier.net/api/parcels/search/{tracking_number}"
    headers = {
        "X-Encrypted-Key": public_token,
        "Origin": base_url,
    }
    response = requests.get(url, headers=headers, timeout=5)
    response_data = response.json()
    tracking_data = response_data["items"][0]["statusHistory"]
    tracking_info = {}
    for step in reversed(tracking_data):
        time_message = step["controlPointDate"]
        tracking_message = step["controlPoint"]
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
        }
    return tracking_info


def track_boxnow(tracking_number: str) -> dict[str, dict[str, str]]:
    url = "https://api-production.boxnow.gr/api/v1/parcels:track"
    json_data = {"parcelId": tracking_number}
    response = requests.post(url, json=json_data, timeout=5)
    response_data = response.json()
    tracking_data = response_data["data"][0]["events"]
    tracking_info = {}
    for step in reversed(tracking_data):
        time_message = step["createTime"]
        location_message = step.get("locationDisplayName", "N/A")
        tracking_message = step["type"]
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
            "location": location_message,
        }
    return tracking_info


def track_cainiao(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://global.cainiao.com/global/detail.json?mailNos={tracking_number}"
    response = requests.get(url, timeout=5)
    response_data = response.json()
    tracking_data = response_data["module"][0]["detailList"]
    tracking_info = {}
    for step in tracking_data:
        time_message = step["timeStr"]
        location_message = step["standerdDesc"]
        tracking_message = step["desc"]
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
            "location": location_message,
        }
    return tracking_info


def track_easymail(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://trackntrace.easymail.gr/{tracking_number}"
    response = requests.get(url, timeout=5)
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
    response = requests.post(url, data=payload, timeout=5)
    response_data = response.json()
    tracking_data = response_data[0]["response"]["out_status"]
    tracking_info = {}
    for step in reversed(tracking_data):
        date = step["out_date"]
        time = step["out_time"]
        time_message = f"{date} {time}"
        location_message = step["out_station"]
        tracking_message = step["out_status_name"]
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
            "location": location_message,
        }
    return tracking_info


def track_eltac(tracking_number: str) -> dict[str, dict[str, str]]:
    url = "https://www.elta-courier.gr/track.php"
    payload = {"number": tracking_number}
    response = requests.post(url, data=payload, timeout=5)
    response_data = json.loads(response.content.decode("utf-8-sig"))
    tracking_data = response_data["result"][tracking_number]["result"]
    tracking_info = {}
    for step in reversed(tracking_data):
        date = step["date"]
        time = step["time"]
        time_message = f"{date} {time}"
        tracking_message = step["status"]
        location_message = step["place"]
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
            "location": location_message,
        }
    return tracking_info


def track_eshop(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://www.e-shop.gr/status.phtml?id={tracking_number}"
    response = requests.get(url, timeout=5)
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
    response = requests.get(url, timeout=5)
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
    response = requests.post(url, headers=headers, json=json_data, timeout=5)
    response_data = response.json()
    tracking_data = response_data["orderHistory"]
    tracking_info = {}
    for step in reversed(tracking_data):
        time_message = step["transactionDate"]
        tracking_message = step["statusDescription"]
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
        }
    return tracking_info


def track_skroutz(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://api.sendx.gr/user/hp/{tracking_number}"
    response = requests.get(url, timeout=5)
    response_data = response.json()
    tracking_data = response_data["trackingDetails"]
    tracking_info = {}
    for step in tracking_data:
        time_message = step["updatedAt"]
        tracking_message = step["description"]
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
        }
    return tracking_info


def track_speedex(tracking_number: str) -> dict[str, dict[str, str]]:
    url = (
        f"http://www.speedex.gr/speedex/NewTrackAndTrace.aspx?number={tracking_number}"
    )
    response = requests.get(url, timeout=5)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    tracking_data = soup.find_all("div", class_="card-header")
    tracking_info = {}
    for step in reversed(tracking_data):
        tracking_message = step.find("h4").text.strip()
        location_message, time_message = step.find("span").text.strip().split(", ")
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
            "location": location_message,
        }
    return tracking_info


def track_sunyou(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://www.sypost.net/queryTrack?trackNumber={tracking_number}&toLanguage=en_US"
    response = requests.get(url, timeout=5)
    jsonp_content = response.text
    start_index = jsonp_content.index("(") + 1
    end_index = jsonp_content.rindex(")")
    json_str = jsonp_content[start_index:end_index]
    json_data = json.loads(json_str)
    tracking_data = json_data["data"][0]["result"]["origin"]["items"]
    tracking_info = {}
    for step in tracking_data:
        tracking_message = step["content"]
        time_message = datetime.datetime.fromtimestamp(
            step["createTime"] // 1000,
            tz=datetime.UTC,
        ).strftime("%Y-%m-%d %H:%M:%S")
        unique_id = generate_unique_id(time_message, tracking_message)
        tracking_info[unique_id] = {
            "time": time_message,
            "message": tracking_message,
        }
    return tracking_info


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
        tracking_info = track_elta("UA108460748HU")
        correct_hash = (
            "6c179f21e6f62b629055d8ab40f454ed02e48b68563913473b857d3638e23b28"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_eltac(self: TestTracking) -> None:
        tracking_info = track_eltac("WI640776981GR")
        correct_hash = (
            "d0c8d0a9f385e87eadad3ff57809525c8af38bbaeb5acc1ea28b205553697d16"
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

    def test_speedex(self: TestTracking) -> None:
        tracking_info = track_speedex("700033415343")
        correct_hash = (
            "9565b1ecde3668df910430c3c2f1213103707d7725beb2f390badbe4cc826055"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_sunyou(self: TestTracking) -> None:
        tracking_info = track_sunyou("SYAE006809461")
        correct_hash = (
            "6b3f9d9d245100498115f0ca3adb5a41e8eb91a0fdeb7551518764a39525446e"
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
        "speedex": track_speedex,
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

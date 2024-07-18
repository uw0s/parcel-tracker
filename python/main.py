from __future__ import annotations

import hashlib
import json
import unittest

import requests
from bs4 import BeautifulSoup


def generate_unique_id(*args: str) -> str:
    combined_string = " ".join(args)
    return hashlib.sha256(combined_string.encode("utf-8")).hexdigest()


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


class TestTracking(unittest.TestCase):
    def test_boxnow(self: TestTracking) -> None:
        tracking_info = track_boxnow("2945812081")
        correct_hash = (
            "5dfa5c690468c03e499e097f7f60e1b042d742024c218d1fd87ae8fba75e62f8"
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
            "adf9291c0e3e783ff093ca8eae6cf4ed97a14c018c1a386b5552abb9156c8d4a"
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
        tracking_info = track_geniki("4836166580")
        correct_hash = (
            "f1d24135dea54816edf954d05d9c39668f5087f67672452ceac38f8d32763fb0"
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


def parcel_tracker(tracking_number: str, shipping: str) -> dict[str, dict[str, str]]:
    tracking_functions = {
        "boxnow": track_boxnow,
        "cainiao": track_cainiao,
        "easymail": track_easymail,
        "elta": track_elta,
        "eltac": track_eltac,
        "eshop": track_eshop,
        "geniki": track_geniki,
        "skroutz": track_skroutz,
        "speedex": track_speedex,
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

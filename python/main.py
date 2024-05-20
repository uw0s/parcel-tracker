from __future__ import annotations

import hashlib
import json
import unittest

import requests
from bs4 import BeautifulSoup


def generate_unique_id(*args: str) -> str:
    combined_string = " ".join(args)
    return hashlib.sha256(combined_string.encode("utf-8")).hexdigest()


def track_easymail(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://trackntrace.easymail.gr/{tracking_number}"
    response = requests.get(
        url,
        timeout=5,
    )
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
    session = requests.Session()
    url = "https://www.elta.gr/trackApi"
    payload = {"code[]": tracking_number, "in_lang": "1"}
    headers = {
        "X-Requested-With": "XMLHttpRequest",
    }
    response = session.post(url, data=payload, headers=headers)
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
    session = requests.Session()
    url = "https://www.elta-courier.gr/track.php"
    payload = {"number": tracking_number}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.elta-courier.gr",
        "DNT": "1",
        "Sec-GPC": "1",
        "Connection": "keep-alive",
        "Referer": f"https://www.elta-courier.gr/search?br={tracking_number}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=1",
    }
    response = session.post(url, data=payload, headers=headers)
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
    response = requests.get(
        url,
        timeout=5,
    )
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
    response = requests.get(
        url,
        timeout=5,
    )
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
            "174ba987ec21bae2d2302737820e1df3c6808415c98209024d8ca63379818bd7"
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
        tracking_info = track_geniki("4805972172")
        correct_hash = (
            "5143d3afd42be9cfb378720f9e2b854806f65593c866676d61d41e414861b3f9"
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
        tracking_info = track_speedex("700030435315")
        correct_hash = (
            "40200f3d4ca71c83f619b5d7ab248633d7eeef371c61bd3c3357271435b60740"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError


def parcel_tracker(tracking_number: str, shipping: str) -> dict[str, dict[str, str]]:
    tracking_functions = {
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

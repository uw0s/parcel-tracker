from __future__ import annotations

import hashlib
import json
import secrets
import time
import unittest

import fire
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
    if app_root is None or not hasattr(app_root, "get"):
        msg = "Could not find app-root element"
        raise ValueError(msg)
    public_token = app_root.get("publictoken")
    if isinstance(public_token, list):
        public_token = public_token[0]
    if public_token is None:
        msg = "Could not find public token"
        raise ValueError(msg)
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


def track_diakinisis(tracking_number: str) -> dict[str, dict[str, str]]:
    url = "https://pod.diakinisis.gr/server_handler_ext.php"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    data = (
        "cmd=srvcmd_ext_tnt&"
        "action=srvaction_getrecordstatus&"
        f"trackingId={tracking_number}&"
        "agreementId=0"
    )
    response = session.post(url, headers=headers, data=data, verify=False)
    tracking_data = response.json()[2]["history"]
    tracking_data = combine_date_time(tracking_data, "action_date", "action_time")
    return parse_tracking_data(
        tracking_data,
        {
            "time": "combined_time",
            "message": "action",
        },
        reverse_order=True,
    )


def track_easymail(tracking_number: str) -> dict[str, dict[str, str]]:
    url = f"https://trackntrace.easymail.gr/{tracking_number}"
    response = session.get(url, timeout=TIMEOUT)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    table_element = soup.find("div", class_="col mobiRemoveMargin")
    if table_element is None or not hasattr(table_element, "find"):
        msg = "Could not find table element"
        raise ValueError(msg)
    tbody_element = table_element.find("tbody")
    if tbody_element is None:
        msg = "Could not find tbody element"
        raise ValueError(msg)
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
    if td_element is None or not hasattr(td_element, "parent"):
        msg = "Could not find td element"
        raise ValueError(msg)
    tr_element = td_element.parent
    if tr_element is None or not hasattr(tr_element, "parent"):
        msg = "Could not find tr element"
        raise ValueError(msg)
    table_element = tr_element.parent
    if table_element is None or not hasattr(table_element, "parent"):
        msg = "Could not find table element"
        raise ValueError(msg)
    tracking_data = table_element.find_all("tr")
    tracking_info = {}
    for step in reversed(tracking_data):
        if step is None or not hasattr(step, "find_all"):
            continue
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
        if step is None or not hasattr(step, "find"):
            continue
        status_div = step.find("div", class_="checkpoint-status")
        tracking_message = (
            status_div.text.replace("Status", "").strip() if status_div else "N/A"
        )
        location_div = step.find("div", class_="checkpoint-location")
        location_message = (
            location_div.text.replace("Location", "").strip() if location_div else "N/A"
        )
        date_div = step.find("div", class_="checkpoint-date")
        date = date_div.text.replace("Date", "").strip() if date_div else ""
        time_div = step.find("div", class_="checkpoint-time")
        time = time_div.text.replace("Time", "").strip() if time_div else ""
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
    response = session.get(url, timeout=TIMEOUT)
    tracking_data = response.json()["trackingDetails"]
    return parse_tracking_data(
        tracking_data,
        {"time": "updatedAt", "message": "description"},
        reverse_order=True,
    )


def track_sunyou(tracking_number: str) -> dict[str, dict[str, str]]:
    ts_ms = int(time.time() * 1000)
    ts_suffix = secrets.randbelow(90000) + 10000
    query_time = f"{ts_ms}-{ts_suffix}"
    url = f"https://www.sypost.net/queryTrack?queryTime={query_time}&trackNumber={tracking_number}&toLanguage=en_US"
    response = session.get(url, timeout=TIMEOUT)
    jsonp_content = response.text
    start_index = jsonp_content.index("(") + 1
    end_index = jsonp_content.rindex(")")
    json_str = jsonp_content[start_index:end_index]
    tracking_data = json.loads(json_str)["data"][0]["result"]["origin"]["items"]
    return parse_tracking_data(
        tracking_data,
        {"time": "createTime", "message": "content"},
        reverse_order=True,
    )


class TestTracking(unittest.TestCase):
    def test_acs(self: TestTracking) -> None:
        tracking_info = track_acs("7644470735")
        correct_hash = (
            "59fee6a692dfe0f282ec4e9db77cb56da756b0e3e41623ca0201aae6422ed8f2"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_boxnow(self: TestTracking) -> None:
        tracking_info = track_boxnow("6324680472")
        correct_hash = (
            "5568ce4681b548530cf13120cbf9ca285cc3f1290bac98c2e0b071a4243d261f"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_cainiao(self: TestTracking) -> None:
        tracking_info = track_cainiao("7639654956")
        correct_hash = (
            "44498bc44a1585ec3fab85e4aa1943defe5075f3a340c1f0b5430f51e9049151"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_diakinisis(self: TestTracking) -> None:
        tracking_info = track_diakinisis("13664278179")
        correct_hash = (
            "2aefa0008cacee4a7847efb7fc63fc3f1c1537d4f45ed3eb24c43ce91d0897ae"
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
        tracking_info = track_elta("PX016217190GR")
        correct_hash = (
            "373806f25167e0e4a2b83ead10d1577c6d30e9c4e47fbb4e550bca32139e620c"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_eltac(self: TestTracking) -> None:
        tracking_info = track_eltac("PX016217190GR")
        correct_hash = (
            "c06e70100369249f55ffdfdb79042ce16258222a10af5b10c35f7dfac6d416b6"
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
        tracking_info = track_geniki("5066866674")
        correct_hash = (
            "13f10274c8be6a8b459b1e4c4bfdaa89e210053a49a8bc4ecbe0c3b87deba7c9"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_skroutz(self: TestTracking) -> None:
        tracking_info = track_skroutz("JLD6ZN7P8YD4W")
        correct_hash = (
            "3115da3bdaa01a354a040e41627f833e80eff82d5ac0d83a756e08d5730e12b5"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError

    def test_sunyou(self: TestTracking) -> None:
        tracking_info = track_sunyou("SYAE006809461")
        correct_hash = (
            "42ca9222219795b01e3077f804bfa016a093799a7e7e78875710188e19125543"
        )
        if next(iter(tracking_info)) != correct_hash:
            raise AssertionError


def parcel_tracker(tracking_number: str, shipping: str) -> dict[str, dict[str, str]]:
    tracking_functions = {
        "acs": track_acs,
        "boxnow": track_boxnow,
        "cainiao": track_cainiao,
        "diakinisis": track_diakinisis,
        "easymail": track_easymail,
        "elta": track_elta,
        "eltac": track_eltac,
        "eshop": track_eshop,
        "geniki": track_geniki,
        "skroutz": track_skroutz,
        "sunyou": track_sunyou,
    }
    track_func = tracking_functions.get(shipping)
    if not track_func:
        msg = f"Unsupported shipping service: {shipping}"
        raise ValueError(msg)
    return track_func(tracking_number)


def main() -> None:
    fire.Fire(parcel_tracker)


if __name__ == "__main__":
    unittest.main()

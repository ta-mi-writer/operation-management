"""Google Calendar API へのインターフェースモジュール (OAuth版)."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote as url_quote
from urllib.parse import unquote

import requests
from google.auth import exceptions as auth_exceptions
from google.auth.transport import requests as auth_requests
from google.oauth2 import credentials
from googleapiclient import discovery

from routing_client import (
  calculate_route,
  extract_address_from_url,
  extract_coordinates,
  generate_maps_url,
  get_coordinates_or_address,
)

# 固定事務所URL
OFFICE_URL = "https://maps.app.goo.gl/yaCYELrM8ouRfLwa7"


def get_calendar_service() -> discovery.Resource:
  """Google Calendar APIサービスを取得する。

  Returns:
    Calendar APIサービスオブジェクト

  Raises:
    ValueError: 認証ファイルが見つからない場合、または無効なトークンの場合
    RuntimeError: トークンのリフレッシュに失敗した場合
  """
  token_path = Path("token.json")

  if not token_path.exists():
    error_msg = "token.jsonが見つかりません: ルートディレクトリに配置してください"
    raise ValueError(error_msg)

  token_data = json.loads(token_path.read_text())

  creds = credentials.Credentials(
    token=token_data.get("token"),
    refresh_token=token_data.get("refresh_token"),
    token_uri=token_data.get("token_uri"),
    client_id=token_data.get("client_id"),
    client_secret=token_data.get("client_secret"),
    scopes=token_data.get(
      "scopes", ["https://www.googleapis.com/auth/calendar.events"]
    ),
  )

  # トークンが期限切れの場合、自動的にリフレッシュ
  if creds.expired and creds.refresh_token:
    try:
      creds.refresh(auth_requests.Request())
    except auth_exceptions.RefreshError as e:
      error_msg = f"トークンのリフレッシュに失敗しました: {e}"
      raise RuntimeError(error_msg) from e

  if not creds.valid:
    error_msg = "無効なトークンです: ローカルで再認証してください"
    raise ValueError(error_msg)

  return discovery.build("calendar", "v3", credentials=creds)


def get_destination_short_name(url: str) -> str:
  """URLから簡略化された住所名を抽出する。

  Args:
    url: Google Maps短縮URL

  Returns:
    簡略化された住所名

  Raises:
    ValueError: URLから住名を抽出できない場合
  """
  response = requests.get(url, allow_redirects=True, timeout=10)
  final_url = response.url

  # 住名抽出
  match = re.search(r"/maps/place/([^/?]+)", final_url)
  if not match:
    error_msg = f"URLから住名を抽出できませんでした: {final_url}"
    raise ValueError(error_msg)

  # URLデコードを適用
  full_address = unquote(match.group(1))

  # 札幌市住址判定
  if "札幌市" in full_address:
    sapporo_pattern = r"札幌市[^市区町村]*?[市区町村]?(.*?[条丁目番地]*)(.*)"
    sapporo_match = re.search(sapporo_pattern, full_address)
    if sapporo_match:
      street_part = sapporo_match.group(1).strip()
      building_part = sapporo_match.group(2).strip()
      if building_part:
        return f"{street_part} {building_part}"
      return street_part

  city_pattern = r"(?:北海道|.*?[都道府県])([^市区町村]*?[市区町村])"
  city_match = re.search(city_pattern, full_address)
  if city_match:
    return city_match.group(1)

  parts = full_address.split("、")
  min_parts = 2
  if len(parts) >= min_parts:
    return parts[0]

  return full_address[:20]


def calculate_notify_minutes(purpose: str, duration_seconds: int | None = None) -> int:
  """移動パターンに応じた通知時間を計算する。

  Args:
    purpose: 移動パターン（送り/現地周辺待機/事務所周辺待機）
    duration_seconds: 所要時間（秒）。事務所周辺待機で使用。

  Returns:
    通知する分数（デフォルトは20、事務所周辺待機は走行時間+15）
  """
  if purpose == "事務所周辺待機" and duration_seconds is not None:
    return (duration_seconds // 60) + 15

  return 20


def create_travel_event(
  purpose: str,
  destination_url: str,
  start_time: datetime,
  duration_seconds: int,
  route_url: str,
  extra_notify: int | None = None,
) -> str:
  """移動予定をGoogleカレンダーに登録する。

  Args:
    purpose: 移動パターン
    destination_url: 到着地URL
    start_time: 開始時刻
    duration_seconds: 所要時間（秒）
    route_url: ルートURL
    extra_notify: 追加通知（分）。0=開始時刻通知、None=追加なし

  Returns:
    登録されたイベントID
  """
  service = get_calendar_service()

  calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
  if not calendar_id:
    error_msg = "GOOGLE_CALENDAR_IDが設定されていません"
    raise ValueError(error_msg)

  dest_name = get_destination_short_name(destination_url)
  title = f"{purpose} {dest_name}"

  end_time = start_time + timedelta(seconds=duration_seconds)

  notify_minutes = calculate_notify_minutes(purpose, duration_seconds)
  reminders = [{"method": "popup", "minutes": notify_minutes}]

  if extra_notify is not None:
    reminders.append({"method": "popup", "minutes": extra_notify})

  event = {
    "summary": title,
    "description": route_url,
    "start": {
      "dateTime": start_time.isoformat(),
      "timeZone": "Asia/Tokyo",
    },
    "end": {
      "dateTime": end_time.isoformat(),
      "timeZone": "Asia/Tokyo",
    },
    "reminders": {
      "useDefault": False,
      "overrides": reminders,
    },
  }

  created = service.events().insert(calendarId=calendar_id, body=event).execute()
  return created.get("id", "")


def parse_args() -> argparse.Namespace:
  """コマンドライン引数を解析する。

  Returns:
    解析結果
  """
  parser = argparse.ArgumentParser(description="Google Calendar 移動予定登録")

  _ = parser.add_argument(
    "--purpose",
    required=True,
    choices=["送り", "現地周辺待機", "事務所周辺待機"],
    help="移動パターン",
  )

  _ = parser.add_argument(
    "--destination",
    required=True,
    help="到着地URL(現地周辺待機の場合は出発地)",
  )

  _ = parser.add_argument(
    "--start-time",
    required=True,
    help='開始時刻 "HH:MM" 形式',
  )

  _ = parser.add_argument(
    "--notify",
    type=int,
    default=None,
    help="追加通知(分)。0=開始時刻通知",
  )

  return parser.parse_args()


def main() -> None:
  """メイン処理を実行する。"""
  args = parse_args()

  jst = timezone(timedelta(hours=9))

  time_obj = datetime.strptime(args.start_time, "%H:%M").time()
  start_time = datetime.combine(datetime.now(jst).date(), time_obj, tzinfo=jst)

  if args.purpose == "事務所周辺待機":
    dest_loc = get_coordinates_or_address(args.destination)
    office_loc = get_coordinates_or_address(OFFICE_URL)
    duration_seconds = calculate_route(office_loc, dest_loc, None)
    adjusted_minutes = (duration_seconds // 60) + 15
    start_time = start_time - timedelta(minutes=adjusted_minutes)
    origin_url = OFFICE_URL
    destination_url = args.destination
  elif args.purpose == "現地周辺待機":
    origin_url = args.destination
    destination_url = OFFICE_URL
    origin_loc = get_coordinates_or_address(origin_url)
    dest_loc = get_coordinates_or_address(destination_url)
    duration_seconds = calculate_route(origin_loc, dest_loc, None)
  else:
    origin_url = OFFICE_URL
    destination_url = args.destination
    origin_loc = get_coordinates_or_address(origin_url)
    dest_loc = get_coordinates_or_address(destination_url)
    duration_seconds = calculate_route(origin_loc, dest_loc, None)

  origin_resp = requests.get(origin_url, allow_redirects=True, timeout=10)
  dest_resp = requests.get(destination_url, allow_redirects=True, timeout=10)

  origin_coords = extract_coordinates(origin_resp.url)
  dest_coords = extract_coordinates(dest_resp.url)

  if origin_coords and dest_coords:
    route_url = generate_maps_url(
      origin_coords[0], origin_coords[1], dest_coords[0], dest_coords[1]
    )
  else:
    origin_addr = extract_address_from_url(origin_resp.url)
    dest_addr = extract_address_from_url(dest_resp.url)
    if origin_addr and dest_addr:
      route_url = (
        f"https://www.google.com/maps/dir/?api=1&origin={url_quote(origin_addr)}"
        f"&destination={url_quote(dest_addr)}&travelmode=driving"
      )
    else:
      route_url = "ルートURLを生成できませんでした"

  event_id = create_travel_event(
    purpose=args.purpose,
    destination_url=destination_url,
    start_time=start_time,
    duration_seconds=duration_seconds,
    route_url=route_url,
    extra_notify=args.notify,
  )

  print(f"イベント登録完了: {event_id}")


if __name__ == "__main__":
  main()

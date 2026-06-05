"""Google Maps短縮URLからplace_idを取得するCLIツール."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from typing import Literal

from additional_schedule import create_delivery_schedule_event
from get_place_id import PlaceResult, RedirectResult, process_maps_url
from get_route_info import get_route_info

# 事務所情報
OFFICE_PLACE_NAME = "すすきのプラザビル"
OFFICE_PLACE_ID = "ChIJSQeomLIpC18RFOdXaFoeZig"


@dataclass
class CalendarEventParams:
  """カレンダーイベント登録パラメータ."""

  summary: str
  route_url: str
  origin_name: str
  dest_name: str
  duration_str: str
  distance_km: float
  start_time_str: str
  reminder_minutes: list[int]


def generate_route_url(
  purpose: Literal["送り", "現地周辺待機", "事務所周辺待機"],
  office_place_id: str,
  office_name: str,
  dest_place_id: str,
  dest_name: str,
) -> tuple[str, str, str]:
  """指定された目的に応じたGoogle MapsルートURLと出発地・目的地名を生成する.

  Returns:
    (url, origin_name, dest_name) のタプルを返す.
  """
  if purpose == "送り":
    # 送り: 事務所 -> 現地
    origin_place_id = office_place_id
    origin_name = office_name
    dest_place_id_val = dest_place_id
    dest_name_val = dest_name
  elif purpose == "現地周辺待機":
    # 現地周辺待機: 現地 -> 事務所
    origin_place_id = dest_place_id
    origin_name = dest_name
    dest_place_id_val = office_place_id
    dest_name_val = office_name
  else:  # 事務所周辺待機
    # 事務所周辺待機: 事務所 -> 現地
    origin_place_id = office_place_id
    origin_name = office_name
    dest_place_id_val = dest_place_id
    dest_name_val = dest_name

  url = (
    f"https://www.google.com/maps/dir/?api=1"
    f"&origin={origin_name}"
    f"&origin_place_id={origin_place_id}"
    f"&destination={dest_name_val}"
    f"&destination_place_id={dest_place_id_val}"
  )
  return url, origin_name, dest_name_val


def calculate_notify_minutes(
  purpose: Literal["送り", "現地周辺待機", "事務所周辺待機"],
  duration_minutes: int,
  distance_km: float,
) -> list[int]:
  """purposeと距離に応じたリマインダー分数リストを返す。

  Args:
    purpose: 移動パターン
    duration_minutes: 所要時間（分）
    distance_km: 距離（キロメートル）

  Returns:
    リマインダー分数のリスト
  """
  distance_threshold_km = 3.0
  buffer_short = 15
  buffer_long = 20

  if purpose == "事務所周辺待機":
    buffer = buffer_short if distance_km <= distance_threshold_km else buffer_long
    return [duration_minutes + buffer]
  return [20]


def get_origin_dest_for_route(
  purpose: Literal["送り", "現地周辺待機", "事務所周辺待機"],
  office_place_id: str,
  dest_place_id: str,
) -> tuple[str, str]:
  """指定された目的に応じた出発地と目的地のPlace IDを返す."""
  if purpose == "送り":
    return office_place_id, dest_place_id
  if purpose == "現地周辺待機":
    return dest_place_id, office_place_id
  # 事務所周辺待機
  return office_place_id, dest_place_id


def parse_args() -> argparse.Namespace:
  """コマンドライン引数をパースする."""
  parser = argparse.ArgumentParser(
    description="Google Maps短縮URLからplace_idを取得します"
  )
  parser.add_argument(
    "--customer-site",
    required=True,
    help="Google Maps short URL (example: https://maps.app.goo.gl/LDfR17Zs6yvuQDyr8)",
  )
  parser.add_argument(
    "--purpose",
    required=True,
    choices=["送り", "現地周辺待機", "事務所周辺待機"],
    help="行動目的を指定してください",
  )
  parser.add_argument(
    "--start-time",
    required=True,
    help='開始時刻 "HH:MM" 形式 (例: 09:30)',
  )
  return parser.parse_args()


def extract_duration_minutes(duration_str: str) -> int:
  """duration文字列から総分数を抽出する."""
  time_parts_hours = 3
  time_parts_minutes = 2
  # HH:MM:SS 形式の場合、最初の数値だけでなく総分数を計算
  time_parts = duration_str.split(":")
  if len(time_parts) == time_parts_hours:
    # HH:MM:SS 形式
    return int(time_parts[0]) * 60 + int(time_parts[1])
  if len(time_parts) == time_parts_minutes:
    # MM:SS 形式
    return int(time_parts[0])
  # その他の形式（例: "30 分"）
  duration_match = re.search(r"(\d+)", duration_str)
  return int(duration_match.group(1)) if duration_match else 0


def register_calendar_event(params: CalendarEventParams) -> None:
  """カレンダーイベントを登録する."""
  try:
    event_id = create_delivery_schedule_event(
      summary=params.summary,
      description=(
        f"配送: {params.origin_name} → {params.dest_name}\n"
        f"{params.route_url}\n"
        f"所要時間: {params.duration_str}\n"
        f"距離: {params.distance_km:.1f} キロメートル"
      ),
      start_time_str=params.start_time_str,
      reminder_minutes=params.reminder_minutes,
    )
    print(f"\n  カレンダー登録完了: {event_id}")
  except (ValueError, RuntimeError) as e:
    print(f"\n  カレンダー登録失敗: {e}")


def process_single_place(
  result: PlaceResult,
  purpose: Literal["送り", "現地周辺待機", "事務所周辺待機"],
  start_time_str: str,
) -> None:
  """単一の場所結果を処理する（ルート生成・情報取得・カレンダー登録）."""
  if not (result.place_id and result.name):
    return

  route_url, origin_name, dest_name = generate_route_url(
    purpose,
    office_place_id=OFFICE_PLACE_ID,
    office_name=OFFICE_PLACE_NAME,
    dest_place_id=result.place_id,
    dest_name=result.name,
  )
  print(f"\n  ルートURL: {route_url}")

  # ルート情報取得
  origin_place_id, dest_place_id_val = get_origin_dest_for_route(
    purpose, OFFICE_PLACE_ID, result.place_id
  )
  route_response = get_route_info(origin_place_id, dest_place_id_val)

  # ルート情報表示
  routes = route_response.routes
  if not routes:
    print("\n  ルート情報が取得できませんでした")
    return

  route = routes[0]
  distance_km = route.distance_meters / 1000
  print(f"\n  ルート距離: {distance_km:.2f}キロメートル")
  print(f"  所要時間: {route.duration}")

  # 所要時間から分数を抽出
  duration_str = str(route.duration)
  duration_minutes = extract_duration_minutes(duration_str)

  # リマインダー分数計算
  reminder_minutes = calculate_notify_minutes(purpose, duration_minutes, distance_km)

  # カレンダー登録
  register_calendar_event(
    params=CalendarEventParams(
      summary=result.name,
      route_url=route_url,
      origin_name=origin_name,
      dest_name=dest_name,
      duration_str=duration_str,
      distance_km=distance_km,
      start_time_str=start_time_str,
      reminder_minutes=reminder_minutes,
    )
  )


def process_place_results(
  redirect_result: RedirectResult,
  place_results: list[PlaceResult],
  purpose: Literal["送り", "現地周辺待機", "事務所周辺待機"],
  start_time_str: str,
) -> None:
  """場所検索結果を処理する."""
  print("\n=== 処理結果 ===")
  if redirect_result.place_name:
    print(f"抽出した場所名: {redirect_result.place_name}")

  if not place_results:
    print("\n場所情報が見つかりませんでした")
    return

  print(f"\n検索結果: {len(place_results)}件")
  for i, result in enumerate(place_results, 1):
    print(f"\n  結果 {i}:")
    if result.place_id:
      print(f"    Place ID: {result.place_id}")
    if result.name:
      print(f"    名前: {result.name}")
    if result.address:
      print(f"    住所: {result.address}")

    process_single_place(result, purpose, start_time_str)


def main() -> None:
  """CLIエントリーポイント."""
  args = parse_args()

  redirect_result, place_results = process_maps_url(args.customer_site)
  process_place_results(
    redirect_result,
    place_results,
    args.purpose,
    args.start_time,
  )


if __name__ == "__main__":
  main()

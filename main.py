"""Google Maps短縮URLからplace_idを取得するCLIツール."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from typing import Literal

from additional_schedule import create_delivery_schedule_event
from get_place_id import (
  PlaceResult,
  RedirectResult,
  calculate_distance_meters,
  get_redirected_url_v2,
  search_with_text_query_v2,
  select_nearest_place,
)
from get_route_info import get_route_info

# 事務所情報
OFFICE_PLACE_NAME = "すすきのプラザビル"
OFFICE_PLACE_ID = "ChIJSQeomLIpC18RFOdXaFoeZig"
TEN_MINUTE_REMINDER_MINUTES = 10


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
  location: str | None = None


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
    f"&origin={origin_name.replace(' ', '%20')}"
    f"&origin_place_id={origin_place_id}"
    f"&destination={dest_name_val.replace(' ', '%20')}"
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
    既存リマインダーに10分前のリマインダーを追加した分数のリスト
  """
  distance_threshold_km = 3.0
  buffer_short = 15
  buffer_long = 20
  min_reminder_minutes = 20

  if purpose == "事務所周辺待機":
    buffer = buffer_short if distance_km <= distance_threshold_km else buffer_long
    base_reminder_minutes = duration_minutes + buffer
    # 距離が3km以下かつアラーム時間が20分未満の場合は20分に設定
    if (
      distance_km <= distance_threshold_km
      and base_reminder_minutes < min_reminder_minutes
    ):
      base_reminder_minutes = min_reminder_minutes
    reminder_minutes = [base_reminder_minutes]
  else:
    reminder_minutes = [20]

  if TEN_MINUTE_REMINDER_MINUTES not in reminder_minutes:
    reminder_minutes.append(TEN_MINUTE_REMINDER_MINUTES)

  return sorted(reminder_minutes)


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


def get_distance_meters_from_redirect_result(
  redirect_result: RedirectResult, result: PlaceResult
) -> float | None:
  """短縮URLの座標と検索候補の距離をメートル単位で返す.

  Args:
      redirect_result: リダイレクト結果
      result: Places APIの検索結果

  Returns:
      距離（メートル）、座標が取れない場合はNone
  """
  if (
    redirect_result.latitude is None
    or redirect_result.longitude is None
    or result.latitude is None
    or result.longitude is None
  ):
    return None

  return calculate_distance_meters(
    redirect_result.latitude,
    redirect_result.longitude,
    result.latitude,
    result.longitude,
  )


def print_place_result(
  index: int,
  redirect_result: RedirectResult,
  result: PlaceResult,
) -> None:
  """検索候補の情報を表示する.

  Args:
      index: 表示番号
      redirect_result: リダイレクト結果
      result: Places APIの検索結果
  """
  print(f"\n  結果 {index}:")
  if result.place_id:
    print(f"    Place ID: {result.place_id}")
  if result.name:
    print(f"    名前: {result.name}")
  if result.address:
    print(f"    住所: {result.address}")

  distance_meters = get_distance_meters_from_redirect_result(redirect_result, result)
  if distance_meters is not None:
    print(f"    基準地点からの距離: {distance_meters:.0f}m")
  else:
    print("    基準地点からの距離: 計算不可")


def print_selected_place_result(result: PlaceResult) -> None:
  """選択した候補の情報を表示する.

  Args:
      result: 選択されたPlaces APIの検索結果
  """
  print("\n選択した候補:")
  if result.place_id:
    print(f"  Place ID: {result.place_id}")
  if result.name:
    print(f"  名前: {result.name}")
  if result.address:
    print(f"  住所: {result.address}")


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
      location=params.location,
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
  location = result.address or result.name
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
      location=location,
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
    print_place_result(i, redirect_result, result)

  selected_result = select_nearest_place(
    place_results, redirect_result.latitude, redirect_result.longitude
  )
  if selected_result is None:
    print("\n場所情報が見つかりませんでした")
    return

  print_selected_place_result(selected_result)
  process_single_place(selected_result, purpose, start_time_str)


def main() -> None:
  """CLIエントリーポイント."""
  args = parse_args()

  redirect_result = get_redirected_url_v2(args.customer_site)
  place_results = (
    search_with_text_query_v2(redirect_result.place_name)
    if redirect_result.place_name
    else []
  )

  process_place_results(
    redirect_result,
    place_results,
    args.purpose,
    args.start_time,
  )


if __name__ == "__main__":
  main()

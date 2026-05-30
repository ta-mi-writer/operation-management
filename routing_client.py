"""Google Maps Routing API v2 へのインターフェースモジュール."""

from __future__ import annotations

import argparse
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote as url_quote
from urllib.parse import unquote

import requests
from google.maps import routing_v2
from google.maps.routing_v2.types import (
  ComputeRoutesRequest,
  Location,
  RouteTravelMode,
  RoutingPreference,
  Waypoint,
)


def extract_coordinates(url: str) -> tuple[float, float] | None:
  """URLから座標を抽出する。

  Args:
    url: GoogleマップURL

  Returns:
    (緯度, 経度) のタプル、または None
  """
  patterns = [
    r"!3d(-?\d+\.\d+)!2d(-?\d+\.\d+)",  # 旧形式: !3d緯度!2d経度
    r"!3d(-?\d+\.\d+).*!2d(-?\d+\.\d+)",  # 旧形式（改良版）
    r"@(-?\d+\.\d+),(-?\d+\.\d+)",  # 新形式: @緯度,経度,ズーム
  ]

  for pattern in patterns:
    lat_match = re.search(pattern, url)
    if lat_match:
      lat = float(lat_match.group(1))
      lng = float(lat_match.group(2))
      return lat, lng
  return None


def extract_address_from_url(url: str) -> str | None:
  """URLから住名を抽出する。

  Args:
    url: GoogleマップURL

  Returns:
    住名文字列、または None
  """
  match = re.search(r"/maps/place/([^/?]+)", url)
  if match:
    return unquote(match.group(1))
  return None


def get_coordinates_or_address(url: str) -> tuple[float, float] | str:
  """短縮URLから座標または住名を抽出する。

  Args:
    url: Googleマップ短縮URL

  Returns:
    (緯度, 経度) のタプル、または住名文字列

  Raises:
    ValueError: URLから座標も住名も抽出できない場合
  """
  # 短縮URLをリダイレクト先までたどる
  response = requests.get(url, allow_redirects=True, timeout=10)
  final_url = response.url

  # 座標優先で抽出
  if coords := extract_coordinates(final_url):
    return coords

  # 座標がなければ住名を抽出
  if address := extract_address_from_url(final_url):
    return address

  error_msg = f"URLから座標も住名も抽出できませんでした: {final_url}"
  raise ValueError(error_msg)


def calculate_route(
  origin: tuple[float, float] | str,
  destination: tuple[float, float] | str,
  departure_time: datetime | None = None,
) -> int:
  """Routing API v2でルートを計算する。

  Args:
    origin: 出発地座標 (緯度, 経度)、または住名文字列
    destination: 到着地座標 (緯度, 経度)、または住名文字列
    departure_time: 出発時刻のdatetimeオブジェクト（省略時は現在時刻）

  Returns:
    所要時間（秒）

  Raises:
    RuntimeError: ルートが見つからない場合
    ValueError: APIキーが設定されていない場合
  """
  api_key = os.getenv("GOOGLE_MAPS_API_KEY") or ""
  if not api_key:
    error_msg = "GOOGLE_MAPS_API_KEYが設定されていません"
    raise ValueError(error_msg)

  client = routing_v2.RoutesClient(client_options={"api_key": api_key})

  # Waypointを適切に生成
  def create_waypoint(loc: tuple[float, float] | str) -> Waypoint:
    if isinstance(loc, str):
      return Waypoint(address=loc)
    return Waypoint(
      location=Location(lat_lng={"latitude": loc[0], "longitude": loc[1]})
    )

  origin_wp = create_waypoint(origin)
  dest_wp = create_waypoint(destination)

  # ComputeRoutesRequestでリクエスト構築
  request = ComputeRoutesRequest(
    origin=origin_wp,
    destination=dest_wp,
    travel_mode=RouteTravelMode.DRIVE,
    routing_preference=RoutingPreference.TRAFFIC_AWARE,
  )

  # departure_time処理
  if departure_time is not None:
    now = datetime.now(timezone(timedelta(hours=9)))
    if departure_time < now:
      departure_time = now + timedelta(minutes=5)
    request.departure_time = departure_time.isoformat()

  # FieldMaskヘッダーを設定（所要時間を取得するために必要）
  response = client.compute_routes(
    request=request,
    metadata=[("x-goog-fieldmask", "routes.duration,routes.legs.duration")],
  )

  # レスポンスから所要時間を取得
  routes = response.routes
  if not routes:
    error_msg = "ルートが見つかりませんでした"
    raise RuntimeError(error_msg)

  route = routes[0]
  legs = route.legs
  if not legs:
    error_msg = "ルート情報にlegsが含まれていません"
    raise RuntimeError(error_msg)

  leg = legs[0]
  duration = leg.duration

  return duration.seconds


def format_duration(seconds: int) -> str:
  """秒を分に変換してフォーマットする。

  Args:
    seconds: 秒数

  Returns:
    "X分" 形式の文字列
  """
  minutes = seconds // 60
  return f"{minutes}分"


def generate_maps_url(
  origin_lat: float,
  origin_lng: float,
  dest_lat: float,
  dest_lng: float,
) -> str:
  """GoogleマップルートURLを生成する。

  Args:
    origin_lat: 出発地緯度
    origin_lng: 出発地経度
    dest_lat: 到着地緯度
    dest_lng: 到着地経度

  Returns:
    GoogleマップルートURL
  """
  origin = f"{origin_lat},{origin_lng}"
  destination = f"{dest_lat},{dest_lng}"
  return f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode=driving"


def parse_args() -> argparse.Namespace:
  """コマンドライン引数を解析する。

  Returns:
    解析結果
  """
  parser = argparse.ArgumentParser(description="Google Maps ルート案内取得アプリ")
  _ = parser.add_argument(
    "--origin",
    required=True,
    help="出発地Googleマップ短縮URL",
  )
  _ = parser.add_argument(
    "--destination",
    required=True,
    help="到着地Googleマップ短縮URL",
  )
  _ = parser.add_argument(
    "--departure",
    help='出発時間 "HH:MM" 形式(省略時は現在時刻)',
  )

  return parser.parse_args()


def main() -> None:
  """メイン処理を実行する。"""
  args = parse_args()

  # 日本時間のタイムゾーン
  jst = timezone(timedelta(hours=9))

  # 出発時刻の処理
  departure_time: datetime | None = None
  departure_val: str | None = args.departure
  if departure_val is not None:
    try:
      time_obj = datetime.strptime(departure_val, "%H:%M").time()
      departure_time = datetime.combine(datetime.now(jst).date(), time_obj, tzinfo=jst)
      now = datetime.now(jst)
      departure_time = max(departure_time, now)
    except ValueError as e:
      msg = f"出発時間の形式が不正です: {args.departure}"
      raise ValueError(msg) from e

  # URLから座標または住名を取得
  origin_url: str = args.origin
  dest_url: str = args.destination
  origin_loc = get_coordinates_or_address(origin_url)
  dest_loc = get_coordinates_or_address(dest_url)

  # ルート計算
  duration_seconds = calculate_route(origin_loc, dest_loc, departure_time)

  # 到着時間計算
  arrival_time = departure_time or datetime.now(jst)
  arrival_time = arrival_time + timedelta(seconds=duration_seconds)

  # 座標取得（URL生成用）
  origin_response = requests.get(origin_url, allow_redirects=True, timeout=10)
  dest_response = requests.get(dest_url, allow_redirects=True, timeout=10)
  origin_coords = extract_coordinates(origin_response.url)
  dest_coords = extract_coordinates(dest_response.url)

  # 住名も取得（座標がない場合のフォールバック）
  origin_address = extract_address_from_url(origin_response.url)
  dest_address = extract_address_from_url(dest_response.url)

  if origin_coords and dest_coords:
    maps_url = generate_maps_url(
      origin_coords[0], origin_coords[1], dest_coords[0], dest_coords[1]
    )
  elif origin_address and dest_address:
    # 住名ベースのURL生成
    encoded_origin = url_quote(origin_address, safe="")
    encoded_dest = url_quote(dest_address, safe="")
    maps_url = f"https://www.google.com/maps/dir/?api=1&origin={encoded_origin}&destination={encoded_dest}&travelmode=driving"
  else:
    maps_url = "URLを生成できませんでした(座標/住名が抽出できないため)"

  # フォーマット出力
  print(f"所要時間: {format_duration(duration_seconds)}")
  print(f"到着時間: {arrival_time.strftime('%Y-%m-%d %H:%M')}")
  print(maps_url)


if __name__ == "__main__":
  main()

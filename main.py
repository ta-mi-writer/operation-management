"""Google Maps ルート案内取得アプリ."""

from __future__ import annotations

import argparse
import os
import re
from datetime import datetime, timedelta, timezone
from typing import TypedDict
from urllib.parse import unquote

import googlemaps  # type: ignore[reportMissingTypeStubs]
import requests


class Geometry(TypedDict):
  """ジオメトリ情報."""

  location: Location


class Location(TypedDict):
  """座標情報."""

  lat: float
  lng: float


class GeocodeResult(TypedDict):
  """ジオコーディング結果."""

  geometry: Geometry


class Duration(TypedDict):
  """所要時間情報."""

  value: int
  text: str


class Leg(TypedDict):
  """ルートの一部（leg）情報."""

  duration: Duration


class Route(TypedDict):
  """ルート情報."""

  legs: list[Leg]


def geocode_address(address: str, gmaps: googlemaps.Client) -> tuple[float, float]:
  """住所から緯度経度を取得する。

  Args:
    address: 住所文字列
    gmaps: Google Mapsクライアント

  Returns:
    (緯度, 経度) のタプル
  """
  result: list[GeocodeResult] = gmaps.geocode(address)  # pyright: ignore[reportAttributeAccessIssue]
  if not result:
    error_msg = f"Geocodingエラー: 住所が見つかりません: {address}"
    raise ValueError(error_msg)

  location = result[0]["geometry"]["location"]
  lat_val = location["lat"]
  lng_val = location["lng"]
  if not isinstance(lat_val, float) or not isinstance(lng_val, float):
    error_msg = "Geocoding結果の型が不正です"
    raise TypeError(error_msg)
  return lat_val, lng_val


def get_address_from_url(url: str) -> str | None:
  """URLから住所を抽出する。

  Args:
    url: GoogleマップURL

  Returns:
    住所文字列（見つからない場合はNone）
  """
  # URLパスから住所を抽出（/maps/place/住所 形式）
  match = re.search(r"/maps/place/([^/?]+)", url)
  if match:
    return unquote(match.group(1))
  return None


def get_coordinates_from_url(url: str, gmaps: googlemaps.Client) -> tuple[float, float]:
  """短縮URLから緯度経度を抽出する。

  Args:
    url: Googleマップ短縮URL
    gmaps: Google Mapsクライアント

  Returns:
    (緯度, 経度) のタプル

  Raises:
    ValueError: URLから緯度経度を抽出できない場合
  """
  # 短縮URLをリダイレクト先までたどる
  response = requests.get(url, allow_redirects=True, timeout=10)
  final_url = response.url

  # URLから緯度経度を抽出
  # 形式: !3d緯度!2d経度
  lat_match = re.search(r"!3d(-?\d+\.\d+)", final_url)
  lng_match = re.search(r"!2d(-?\d+\.\d+)", final_url)

  if lat_match and lng_match:
    latitude = float(lat_match.group(1))
    longitude = float(lng_match.group(1))
    return latitude, longitude

  # 座標が見つからない場合は住所からGeocoding
  address = get_address_from_url(final_url)
  if address:
    return geocode_address(address, gmaps)

  msg = "URLから緯度経度を抽出できませんでした"
  error_msg = f"{msg}: {final_url}"
  raise ValueError(error_msg)


def calculate_route(
  origin: tuple[float, float],
  destination: tuple[float, float],
  departure_time: datetime | None = None,
  gmaps: googlemaps.Client | None = None,
) -> Route:
  """Directions APIでルートを計算する。

  Args:
    origin: 出発地座標 (緯度, 経度)
    destination: 到着地座標 (緯度, 経度)
    departure_time: 出発時刻（省略時は現在時刻）
    gmaps: Google Mapsクライアント

  Returns:
    ルート情報
  """
  if gmaps is None:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or ""
    if not api_key:
      error_msg = "GOOGLE_MAPS_API_KEYが設定されていません"
      raise ValueError(error_msg)
    gmaps = googlemaps.Client(key=api_key)

  # Directions APIでルート計算
  result: list[Route] = gmaps.directions(  # pyright: ignore[reportAttributeAccessIssue]
    origin,
    destination,
    mode="driving",
    departure_time=departure_time,
    avoid=["tolls", "highways", "ferries"],
  )

  if not result:
    error_msg = "ルートが見つかりませんでした"
    raise RuntimeError(error_msg)

  return result[0]  # pyright: ignore[reportUnknownVariableType]


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

  # APIキーの確認
  api_key = os.getenv("GOOGLE_MAPS_API_KEY") or ""
  if not api_key:
    error_msg = "GOOGLE_MAPS_API_KEYが設定されていません"
    raise ValueError(error_msg)

  # Google Mapsクライアントの初期化
  gmaps = googlemaps.Client(key=api_key)

  # 日本時間のタイムゾーン
  jst = timezone(timedelta(hours=9))

  # 出発時刻の処理
  departure_time: datetime | None = None
  departure_val: str | None = args.departure
  if departure_val is not None:
    try:
      time_obj = datetime.strptime(departure_val, "%H:%M").time()
      departure_time = datetime.combine(datetime.now(jst).date(), time_obj, tzinfo=jst)
      # 過去の時間の場合は現在時刻を使用
      now = datetime.now(jst)
      departure_time = max(departure_time, now)
    except ValueError as e:
      msg = f"出発時間の形式が不正です: {args.departure}"
      raise ValueError(msg) from e

  # URLから緯度経度を取得
  origin: str = args.origin  # pyright: ignore[reportAny]
  destination: str = args.destination  # pyright: ignore[reportAny]
  origin_lat, origin_lng = get_coordinates_from_url(origin, gmaps)
  dest_lat, dest_lng = get_coordinates_from_url(destination, gmaps)

  # ルート計算
  route = calculate_route(
    (origin_lat, origin_lng),
    (dest_lat, dest_lng),
    departure_time,
    gmaps,
  )

  # 結果取得
  # directions APIの結果から所要時間を取得
  legs = route["legs"]
  if not legs:
    error_msg = "ルート情報にlegsが含まれていません"
    raise RuntimeError(error_msg)
  leg: Leg = legs[0]
  duration = leg["duration"]
  duration_value = duration["value"]
  if not isinstance(duration_value, int):
    error_msg = "所要時間の型が不正です"
    raise TypeError(error_msg)
  duration_seconds: int = duration_value
  arrival_time = departure_time or datetime.now(jst)
  arrival_time = arrival_time + timedelta(seconds=duration_seconds)

  # フォーマット出力
  print(f"所要時間: {format_duration(duration_seconds)}")
  print(f"到着時間: {arrival_time.strftime('%Y-%m-%d %H:%M')}")
  print(generate_maps_url(origin_lat, origin_lng, dest_lat, dest_lng))


if __name__ == "__main__":
  main()

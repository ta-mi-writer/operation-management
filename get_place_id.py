"""URLリダイレクトとGoogle Places API Text Query検索のサンプルコード."""

from __future__ import annotations

import argparse
import math
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

import requests

# Google Places API用
from google.api_core.exceptions import GoogleAPIError
from google.maps import places_v1
from google.maps.places_v1.types import Circle, SearchTextRequest
from google.type import latlng_pb2


@dataclass
class PlaceResult:
  """検索結果を表すデータクラス."""

  place_id: str | None = None
  name: str | None = None
  address: str | None = None
  latitude: float | None = None
  longitude: float | None = None
  types: list[str] | None = None  # type: ignore[assignment]


@dataclass
class RedirectResult:
  """リダイレクト結果を表すデータクラス."""

  final_url: str | None = None
  place_name: str | None = None
  latitude: float | None = None
  longitude: float | None = None
  redirect_history: list[dict[str, Any]] | None = None


def extract_maps_url_info(url: str) -> tuple[str | None, float | None, float | None]:
  """Google Maps URLから場所名と座標を抽出する.

  Args:
      url: Google MapsのURL文字列

  Returns:
      (place_name, latitude, longitude)のタプル
  """
  decoded_url = unquote(url)

  place_match = re.search(r"place/([^/]+)/@", decoded_url)
  place_name = place_match.group(1).replace("+", " ") if place_match else None

  coordinate_match = re.search(r"@(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)", decoded_url)
  if not coordinate_match:
    return place_name, None, None

  latitude = float(coordinate_match.group(1))
  longitude = float(coordinate_match.group(2))
  return place_name, latitude, longitude


def calculate_distance_meters(
  latitude1: float,
  longitude1: float,
  latitude2: float,
  longitude2: float,
) -> float:
  """Haversine distanceを使用して2地点間の距離をメートル単位で返す.

  Args:
      latitude1: 1地点目の緯度
      longitude1: 1地点目の経度
      latitude2: 2地点目の緯度
      longitude2: 2地点目の経度

  Returns:
      2地点間の距離（メートル）
  """
  earth_radius_meters = 6371000
  phi1 = math.radians(latitude1)
  phi2 = math.radians(latitude2)
  delta_phi = math.radians(latitude2 - latitude1)
  delta_lambda = math.radians(longitude2 - longitude1)

  a = (
    math.sin(delta_phi / 2) ** 2
    + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
  )
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
  return earth_radius_meters * c


def select_nearest_place(
  place_results: list[PlaceResult],
  latitude: float | None,
  longitude: float | None,
) -> PlaceResult | None:
  """座標に最も近い場所を検索結果から1件選択する.

  Args:
      place_results: Places APIの検索結果
      latitude: 基準地点の緯度
      longitude: 基準地点の経度

  Returns:
      最も近い場所、またはNone
  """
  if not place_results:
    return None

  if latitude is None or longitude is None:
    print("警告: URLから座標を抽出できませんでした。検索結果の1件目を使用します。")
    return place_results[0]

  candidates: list[tuple[float, PlaceResult]] = []
  for result in place_results:
    if result.latitude is None or result.longitude is None:
      continue
    distance_meters = calculate_distance_meters(
      latitude, longitude, result.latitude, result.longitude
    )
    candidates.append((distance_meters, result))

  if not candidates:
    print("警告: 検索候補の座標が取得できませんでした。検索結果の1件目を使用します。")
    return place_results[0]

  return min(candidates, key=lambda item: item[0])[1]


def get_redirected_url(
  short_url: str,
) -> tuple[str | None, str | None]:
  """短いURLをリダイレクトして本来のURLを取得する."""
  headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0 Safari/537.36"
  }

  final_url: str | None = None
  place_name: str | None = None
  redirect_history: list[dict[str, Any]] = []

  try:
    response = requests.get(
      short_url, headers=headers, allow_redirects=True, timeout=10
    )
    final_url = response.url

    print("リダイレクト履歴:")
    for i, resp in enumerate(response.history):
      print(f"  {i + 1}. {resp.url} -> {resp.status_code}")
      redirect_history.append({"url": resp.url, "status_code": resp.status_code})

    print(f"\n最終的なURL: {final_url}")

    decoded_url = unquote(final_url)
    print(f"\nデコード後のURL: {decoded_url}")

    place_name, latitude, longitude = extract_maps_url_info(decoded_url)
    if place_name:
      print(f"\n抽出した場所名: {place_name}")
    if latitude is not None and longitude is not None:
      print(f"抽出した座標: {latitude}, {longitude}")

  except requests.exceptions.RequestException as e:
    print(f"エラーが発生しました: {e}")

  return final_url, place_name


def get_redirected_url_v2(short_url: str) -> RedirectResult:
  """リダイレクト結果を構造化して返す関数（ライブラリ向け）."""
  final_url, place_name = get_redirected_url(short_url)
  latitude = None
  longitude = None
  if final_url:
    place_name, latitude, longitude = extract_maps_url_info(final_url)
  return RedirectResult(
    final_url=final_url,
    place_name=place_name,
    latitude=latitude,
    longitude=longitude,
    redirect_history=None,  # 後方互換性のため
  )


def get_api_key(api_key: str | None = None) -> str | None:
  """Get Google Maps API key from parameter or environment variable."""
  if api_key is None:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
  return api_key


def search_with_text_query_v2(
  place_name: str,
  api_key: str | None = None,
  latitude: float | None = None,
  longitude: float | None = None,
) -> list[PlaceResult]:
  """Google Places API の Text Query を使用して場所を検索する（ライブラリ向け）."""
  api_key = get_api_key(api_key)

  if not api_key:
    return []

  client = places_v1.PlacesClient(client_options={"api_key": api_key})
  request_kwargs: dict[str, Any] = {
    "text_query": place_name,
    "language_code": "ja",
    "region_code": "JP",
    "max_result_count": 5,
  }
  if latitude is not None and longitude is not None:
    bias_radius_meters = 5000
    request_kwargs["location_bias"] = SearchTextRequest.LocationBias(
      circle=Circle(
        center=latlng_pb2.LatLng(latitude=latitude, longitude=longitude),
        radius=bias_radius_meters,
      )
    )
  request = SearchTextRequest(**request_kwargs)

  results: list[PlaceResult] = []
  try:
    response = client.search_text(
      request,
      metadata=[
        (
          "x-goog-fieldmask",
          "places.id,places.displayName,places.formattedAddress,"
          "places.location,places.types",
        )
      ],
    )

    if response.places:
      for place in response.places:
        result = PlaceResult(
          place_id=place.id,
          name=(
            place.display_name.text
            if place.display_name and hasattr(place.display_name, "text")
            else str(place.display_name)
            if place.display_name
            else None
          ),
          address=place.formatted_address,
          latitude=place.location.latitude if place.location else None,
          longitude=place.location.longitude if place.location else None,
          types=list(place.types) if place.types else None,  # type: ignore[assignment]
        )
        results.append(result)

  except GoogleAPIError as e:
    print(f"Google API エラー: {e}")

  return results


def search_with_text_query(place_name: str, api_key: str | None = None) -> None:
  """Google Places API の Text Query を使用して場所を検索する."""
  results = search_with_text_query_v2(place_name, api_key)

  if not results:
    print("警告: Google Maps API キーが必要です")
    print(
      "環境変数 GOOGLE_MAPS_API_KEY を設定するか、api_key パラメータを渡してください"
    )
    return

  print(f"\nテキストクエリ検索結果: '{place_name}'")
  for i, result in enumerate(results, 1):
    print(f"\n  結果 {i}:")
    print(f"    Place ID: {result.place_id}")
    print(f"    名前: {result.name}")
    print(f"    住所: {result.address}")
    if result.latitude and result.longitude:
      print(f"    座標: {result.latitude}, {result.longitude}")
    if result.types:
      print(f"    タイプ: {', '.join(result.types)}")


def process_maps_url(
  short_url: str, api_key: str | None = None
) -> tuple[RedirectResult, list[PlaceResult]]:
  """Google Maps short URLを処理し、リダイレクト結果と場所情報を返す.

  両方の機能を統合したライブラリ向け関数.

  Args:
      short_url: Google Maps short URL
      api_key: Google Maps API key (環境変数からも取得可能)

  Returns:
      tuple: (RedirectResult, list[PlaceResult])
  """
  redirect_result = get_redirected_url_v2(short_url)

  if redirect_result.place_name:
    place_results = search_with_text_query_v2(redirect_result.place_name, api_key)
  else:
    place_results = []

  return redirect_result, place_results


def main() -> None:
  """CLIエントリーポイント."""
  parser = argparse.ArgumentParser(
    description="Google Maps short URLをリダイレクトしてPlace IDを取得します"
  )
  parser.add_argument(
    "short_url",
    help="Google Maps short URL (example: https://maps.app.goo.gl/LDfR17Zs6yvuQDyr8)",
  )
  parser.add_argument(
    "--api-key",
    help="Google Maps API key (デフォルト: 環境変数 GOOGLE_MAPS_API_KEY)",
  )
  args = parser.parse_args()

  final_url, place_name = get_redirected_url(args.short_url)

  if final_url:
    print(f"\n取得成功: {final_url}")

  # Place API でのテキストクエリ検索（APIキーが必要）
  if place_name:
    search_with_text_query(place_name, args.api_key)


if __name__ == "__main__":
  main()

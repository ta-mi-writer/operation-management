"""URLリダイレクトとGoogle Places API Text Query検索のサンプルコード."""

from __future__ import annotations

import argparse
import os
import re
from urllib.parse import unquote

import requests

# Google Places API用
from google.api_core.exceptions import GoogleAPIError
from google.maps import places_v1
from google.maps.places_v1.types import SearchTextRequest


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

  try:
    response = requests.get(
      short_url, headers=headers, allow_redirects=True, timeout=10
    )
    final_url = response.url

    print("リダイレクト履歴:")
    for i, resp in enumerate(response.history):
      print(f"  {i + 1}. {resp.url} -> {resp.status_code}")

    print(f"\n最終的なURL: {final_url}")

    decoded_url = unquote(final_url)
    print(f"\nデコード後のURL: {decoded_url}")

    place_match = re.search(r"place/([^/]+)/@", decoded_url)
    if place_match:
      place_name = place_match.group(1).replace("+", " ")
      print(f"\n抽出した場所名: {place_name}")

  except requests.exceptions.RequestException as e:
    print(f"エラーが発生しました: {e}")

  return final_url, place_name


def search_with_text_query(place_name: str, api_key: str | None = None) -> None:
  """Google Places API の Text Query を使用して場所を検索する."""
  # APIキーの確認
  if api_key is None:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

  if not api_key:
    print("警告: Google Maps API キーが必要です")
    print(
      "環境変数 GOOGLE_MAPS_API_KEY を設定するか、api_key パラメータを渡してください"
    )
    return

  # クライアント初期化
  client = places_v1.PlacesClient(client_options={"api_key": api_key})

  # 検索リクエスト作成
  request = SearchTextRequest(
    text_query=place_name,
    language_code="ja",
    region_code="JP",
    max_result_count=5,
  )

  # 検索実行
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

    print(f"\nテキストクエリ検索結果: '{place_name}'")
    if response.places:
      for i, place in enumerate(response.places, 1):
        print(f"\n  結果 {i}:")
        if place.id:
          print(f"    Place ID: {place.id}")
        if place.display_name:
          # DisplayInfoオブジェクトの text 属性を使用
          display_text = (
            place.display_name.text
            if hasattr(place.display_name, "text")
            else str(place.display_name)
          )
          print(f"    名前: {display_text}")
        if place.formatted_address:
          print(f"    住所: {place.formatted_address}")
        if place.location:
          print(f"    座標: {place.location.latitude}, {place.location.longitude}")
        if place.types:
          print(f"    タイプ: {', '.join(place.types)}")

  except GoogleAPIError as e:
    print(f"Google API エラー: {e}")


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Google Maps short URLをリダイレクトしてPlace IDを取得します"
  )
  parser.add_argument(
    "short_url", help="Google Maps short URL (example: https://maps.app.goo.gl/LDfR17Zs6yvuQDyr8)"
  )
  args = parser.parse_args()

  result, place_name = get_redirected_url(args.short_url)

  if result:
    print(f"\n取得成功: {result}")

  # Place API でのテキストクエリ検索（APIキーが必要）
  if place_name:
    search_with_text_query(place_name)

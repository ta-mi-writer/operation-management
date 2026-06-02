"""Google Maps短縮URLからplace_idを取得するCLIツール."""

from __future__ import annotations

import argparse
from typing import Literal

from get_place_id import process_maps_url

# 事務所情報
OFFICE_PLACE_NAME = "すすきのプラザビル"
OFFICE_PLACE_ID = "ChIJSQeomLIpC18RFOdXaFoeZig"

# 出発地（千歳ステーションホテル）
ORIGIN_PLACE_NAME = "千歳ステーションホテル"
ORIGIN_PLACE_ID = "ChIJdxpz46kgdV8RLSX3Ilrf6no"


def generate_route_url(
  purpose: Literal["送り", "現地周辺待機", "事務所周辺待機"],
  office_place_id: str,
  office_name: str,
  dest_place_id: str,
  dest_name: str,
) -> str:
  """指定された目的に応じたGoogle MapsルートURLを生成する."""
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
  else:  # 事募所周辺待機
    # 事務所周辺待機: 事務所 -> 現地
    origin_place_id = office_place_id
    origin_name = office_name
    dest_place_id_val = dest_place_id
    dest_name_val = dest_name

  return (
    f"https://www.google.com/maps/dir/?api=1"
    f"&origin={origin_name}"
    f"&origin_place_id={origin_place_id}"
    f"&destination={dest_name_val}"
    f"&destination_place_id={dest_place_id_val}"
  )


def main() -> None:
  """CLIエントリーポイント."""
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
  args = parser.parse_args()

  redirect_result, place_results = process_maps_url(args.customer_site)

  print("\n=== 処理結果 ===")
  if redirect_result.place_name:
    print(f"抽出した場所名: {redirect_result.place_name}")

  if place_results:
    print(f"\n検索結果: {len(place_results)}件")
    for i, result in enumerate(place_results, 1):
      print(f"\n  結果 {i}:")
      if result.place_id:
        print(f"    Place ID: {result.place_id}")
      if result.name:
        print(f"    名前: {result.name}")
      if result.address:
        print(f"    住所: {result.address}")

      # ルートURL生成
      if result.place_id and result.name:
        route_url = generate_route_url(
          args.purpose,
          office_place_id=OFFICE_PLACE_ID,
          office_name=OFFICE_PLACE_NAME,
          dest_place_id=result.place_id,
          dest_name=result.name,
        )
        print(f"\n  ルートURL: {route_url}")
  else:
    print("\n場所情報が見つかりませんでした")


if __name__ == "__main__":
  main()

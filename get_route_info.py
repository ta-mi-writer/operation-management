"""Google Maps Routing API v2を使用してルート情報を取得する."""

import os
import re

from google.maps import routing_v2
from google.maps.routing_v2.types import (
  ComputeRoutesRequest,
  RouteLabel,
  RouteModifiers,
  RouteTravelMode,
  RoutingPreference,
  Waypoint,
)


def get_route_info() -> routing_v2.ComputeRoutesResponse:
  """出発地から目的地までのルート情報を取得する.

  Returns:
      ComputeRoutesResponse: ルート情報のレスポンス
  """
  api_key = os.getenv("GOOGLE_MAPS_API_KEY") or ""

  client = routing_v2.RoutesClient(client_options={"api_key": api_key})

  # Place IDをWaypointに変換
  origin_wp = Waypoint(place_id="ChIJSQeomLIpC18RFOdXaFoeZig")
  dest_wp = Waypoint(place_id="ChIJT2FKyUMrC18RbsBcsnO5URo")

  # ComputeRoutesRequestでリクエスト構築
  # 注: FUEL_EFFICIENTは日本国内未サポートのため、TRAFFIC_AWARE_OPTIMALを使用
  request = ComputeRoutesRequest(
    origin=origin_wp,
    destination=dest_wp,
    travel_mode=RouteTravelMode.DRIVE,
    routing_preference=RoutingPreference.TRAFFIC_AWARE_OPTIMAL,
    route_modifiers=RouteModifiers(
      avoid_ferries=True,
      avoid_tolls=True,  # 有料道路を回避
      avoid_highways=True,  # 高速道路を回避
    ),
  )

  # FieldMaskヘッダーを設定
  field_mask = (
    "routes.duration,routes.distanceMeters,routes.legs.steps,routes.routeLabels"
  )
  return client.compute_routes(
    request=request,
    metadata=[("x-goog-fieldmask", field_mask)],
  )


def main() -> None:
  """メイン関数."""
  api_key = os.getenv("GOOGLE_MAPS_API_KEY") or ""
  if not api_key:
    print("GOOGLE_MAPS_API_KEYが環境変数に設定されていません")
    return

  # ルート情報取得
  response = get_route_info()

  # 結果出力
  routes = response.routes
  if routes:
    # 燃料効率ルートを優先的に選択（サポートされている場合）
    eco_route = None
    for route in routes:
      if RouteLabel.FUEL_EFFICIENT in route.route_labels:
        eco_route = route
        break

    # エコルートがない場合は最初のルートを使用
    route = eco_route or routes[0]

    # 総距離・時間
    distance = route.distance_meters
    duration = route.duration
    print(f"ルート距離: {distance}メートル")
    print(f"所要時間: {duration}")

    # ルート手順
    if route.legs:
      for leg_idx, leg in enumerate(route.legs):
        print(f"\n区間 {leg_idx + 1}:")
        for step_idx, step in enumerate(leg.steps):
          nav_instruction = step.navigation_instruction
          instruction = nav_instruction.instructions if nav_instruction else ""
          clean_instruction = re.sub(r"<[^>]+>", "", instruction)
          print(f"  ステップ {step_idx + 1}: {clean_instruction}")
          print(f"    距離: {step.distance_meters}メートル")
  else:
    print("ルートが見つかりませんでした")


if __name__ == "__main__":
  main()

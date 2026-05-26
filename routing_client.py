"""Google Maps Routing API v2 へのインターフェースモジュール."""

from __future__ import annotations

import os

from google.maps import routing_v2
from google.maps.routing_v2.types import (
    ComputeRoutesRequest,
    Location,
    RouteTravelMode,
    RoutingPreference,
    Waypoint,
)


def calculate_route(
    origin: tuple[float, float],
    destination: tuple[float, float],
    departure_time: str | None = None,
) -> int:
    """Routing API v2でルートを計算する。

    Args:
        origin: 出発地座標 (緯度, 経度)
        destination: 到着地座標 (緯度, 経度)
        departure_time: 出発時刻のISO8601形式文字列（省略時は現在時刻）

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

    client = routing_v2.RoutesClient(
        client_options={"api_key": api_key}
    )

    # Waypoint形式で座標を指定
    origin_wp = Waypoint(
        location=Location(lat_lng={"latitude": origin[0], "longitude": origin[1]})
    )
    dest_wp = Waypoint(
        location=Location(
            lat_lng={"latitude": destination[0], "longitude": destination[1]}
        )
    )

    # ComputeRoutesRequestでリクエスト構築
    request = ComputeRoutesRequest(
        origin=origin_wp,
        destination=dest_wp,
        travel_mode=RouteTravelMode.DRIVE,
        routing_preference=RoutingPreference.TRAFFIC_AWARE,
    )

    if departure_time is not None:
        request.departure_time = departure_time

    # FieldMaskヘッダーを設定（所要時間を取得するために必要）
    response = client.compute_routes(
        request=request,
        metadata=[("x-goog-fieldmask", "routes.duration,routes.legs.duration")]
    )

    # レスポンスから所要時間を取得
    routes = response.routes  # pyright: ignore[reportAttributeAccessIssue]
    if not routes:
        error_msg = "ルートが見つかりませんでした"
        raise RuntimeError(error_msg)

    route = routes[0]
    legs = route.legs  # pyright: ignore[reportAttributeAccessIssue]
    if not legs:
        error_msg = "ルート情報にlegsが含まれていません"
        raise RuntimeError(error_msg)

    leg = legs[0]
    duration = leg.duration  # pyright: ignore[reportAttributeAccessIssue]

    return duration.seconds  # pyright: ignore[reportAttributeAccessIssue]

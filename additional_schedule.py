"""Google Calendar への配送スケジュール追加モジュール."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth import exceptions as auth_exceptions
from google.auth.transport import requests as auth_requests
from google.oauth2 import credentials
from googleapiclient import discovery

# Load .env file
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
  for line in _env_path.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
      key, _, value = line.partition("=")
      os.environ.setdefault(key, value)


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
      # リフレッシュ後のトークンを保存
      token_path.write_text(
        json.dumps(
          {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
          },
          indent=2,
        )
      )
    except auth_exceptions.RefreshError as e:
      error_msg = f"トークンのリフレッシュに失敗しました: {e}"
      raise RuntimeError(error_msg) from e

  if not creds.valid:
    error_msg = "無効なトークンです: ローカルで再認証してください"
    raise ValueError(error_msg)

  return discovery.build("calendar", "v3", credentials=creds)


def create_delivery_schedule_event(
  summary: str,
  description: str,
  start_time_str: str,
  reminder_minutes: list[int],
  location: str | None = None,
) -> str:
  """配送スケジュールをGoogleカレンダーに登録する。

  Args:
    summary: イベントのタイトル
    description: イベントの説明
    start_time_str: 開始時刻（"HH:MM"形式の文字列）
    reminder_minutes: リマインダーのminutes値のリスト
    location: イベントの場所

  Returns:
    登録されたイベントID
  """
  service = get_calendar_service()

  calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
  if not calendar_id:
    error_msg = "GOOGLE_CALENDAR_IDが設定されていません"
    raise ValueError(error_msg)

  # 指定された時刻を開始時刻とする
  jst = timezone(timedelta(hours=9))
  start_time = datetime.combine(
    datetime.now(jst).date(),
    datetime.strptime(start_time_str, "%H:%M").time(),
    tzinfo=jst,
  )

  # 終了時刻は1時間後
  end_time = start_time + timedelta(hours=1)

  # remindersの構築
  overrides = [{"method": "popup", "minutes": minutes} for minutes in reminder_minutes]

  event = {
    "summary": summary,
    "description": description,
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
      "overrides": overrides,
    },
  }
  if location:
    event["location"] = location

  created = service.events().insert(calendarId=calendar_id, body=event).execute()
  return created.get("id", "")


def main() -> None:
  """メイン処理を実行する."""
  event_id = create_delivery_schedule_event(
    summary="配送スケジュール",
    description="ここにルートのURLが入ります",
    start_time_str="23:30",
    reminder_minutes=[20],
  )
  print(f"配送スケジュールを追加しました: {event_id}")


if __name__ == "__main__":
  main()

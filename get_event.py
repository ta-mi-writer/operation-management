"""Googleカレンダーからイベントを取得するスクリプト."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient import discovery


def get_calendar_service() -> discovery.Resource:
  """Google Calendar APIサービスを取得する。

  Returns:
    Calendar APIサービスオブジェクト

  Raises:
    ValueError: 認証ファイルが見つからない場合
  """
  key_path = os.getenv("GOOGLE_KEY_FILE", "service_account.json")

  if not Path(key_path).exists():
    error_msg = f"サービスアカウントキーが見つかりません: {key_path}"
    raise ValueError(error_msg)

  credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/calendar.events"],
  )

  return discovery.build("calendar", "v3", credentials=credentials)


def get_event(event_id: str) -> dict:
  """Googleカレンダーからイベントを取得する。

  Args:
    event_id: 取得するイベントのID

  Returns:
    イベント情報の辞書

  Raises:
    ValueError: カレンダーIDが設定されていない場合
  """
  service = get_calendar_service()

  calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
  if not calendar_id:
    error_msg = "GOOGLE_CALENDAR_IDが設定されていません"
    raise ValueError(error_msg)

  return service.events().get(calendarId=calendar_id, eventId=event_id).execute()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Googleカレンダーからイベントを取得する")
  parser.add_argument("event_id", help="取得するイベントのID")
  args = parser.parse_args()

  event = get_event(args.event_id)
  print(json.dumps(event, indent=2, ensure_ascii=False))

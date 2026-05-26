#!/usr/bin/env python3
"""Context7 API client for searching and retrieving documentation context."""

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE_URL = "https://context7.com/api"
API_V2 = f"{API_BASE_URL}/v2"

DEFAULT_QUERY = "overview"


def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.environ.get("CONTEXT7_API_KEY")
    if not api_key:
        msg = "エラー: CONTEXT7_API_KEY 環境変数が設定されていません。"
        print(msg, file=sys.stderr)
        sys.exit(1)
    return api_key


def make_request(endpoint: str, params: dict | None = None) -> dict:
    """Make an authenticated API request."""
    url = f"{endpoint}"
    if params:
        url = f"{endpoint}?{urlencode(params)}"

    api_key = get_api_key()
    request = Request(url, headers={"Authorization": f"Bearer {api_key}"})  # noqa: S310

    try:
        with urlopen(request) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_data = json.loads(error_body)
            error_msg = error_data.get("message", str(e))
        except json.JSONDecodeError:
            error_msg = error_body or str(e)
        print(f"エラー ({e.code}): {error_msg}", file=sys.stderr)
        sys.exit(e.code)
    except URLError as e:
        print(f"接続エラー: {e.reason}", file=sys.stderr)
        sys.exit(1)


def search_library(name: str, query: str | None = None) -> dict:
    """Search for a library by name."""
    params: dict = {"libraryName": name}
    if query:
        params["query"] = query
    return make_request(f"{API_V2}/libs/search", params)


def get_context(
    library_id: str, query: str | None = None, output_type: str = "json"
) -> dict | str:
    """Get documentation context for a library."""
    params: dict = {"libraryId": library_id}
    if query:
        params["query"] = query
    else:
        params["query"] = DEFAULT_QUERY
    params["type"] = output_type

    url = f"{API_V2}/context?{urlencode(params)}"
    api_key = get_api_key()
    request = Request(url, headers={"Authorization": f"Bearer {api_key}"})  # noqa: S310

    try:
        with urlopen(request) as response:  # noqa: S310
            content = response.read().decode("utf-8")
            if output_type == "txt":
                return content
            return json.loads(content)
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_data = json.loads(error_body)
            error_msg = error_data.get("message", str(e))
        except json.JSONDecodeError:
            error_msg = error_body or str(e)
        print(f"\nエラー ({e.code}): {error_msg}", file=sys.stderr)
        print("\nヒント: ", file=sys.stderr)
        print(
            "  - ライブラリIDが正しいか確認してください (例: /owner/repo)",
            file=sys.stderr,
        )
        print(
            "  - APIキーが有効か確認してください (.env の CONTEXT7_API_KEY)",
            file=sys.stderr,
        )
        print(
            "  - 別のクエリを試してみてください: --query 'getting started'",
            file=sys.stderr,
        )
        sys.exit(e.code)
    except URLError as e:
        print(f"\n接続エラー: {e.reason}", file=sys.stderr)
        print("\nヒント:", file=sys.stderr)
        print("  - インターネット接続を確認してください", file=sys.stderr)
        print("  - APIエンドポイントが利用可能か確認してください", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Context7 API client for documentation lookup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # search subcommand
    search_parser = subparsers.add_parser("search", help="Search for libraries")
    search_parser.add_argument("name", help="Library name to search for")
    search_parser.add_argument("--query", "-q", help="Search query")
    search_parser.add_argument(
        "--type", "-t", choices=["json", "txt"], default="json", help="Output format"
    )

    # context subcommand
    context_parser = subparsers.add_parser(
        "context", help="Get documentation context"
    )
    context_parser.add_argument(
        "library_id", help="Library ID (e.g., /vercel/next.js)"
    )
    context_parser.add_argument(
        "--query", "-q", help="Query for specific documentation"
    )
    context_parser.add_argument(
        "--type", "-t", choices=["json", "txt"], default="json", help="Output format"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "search":
        result = search_library(args.name, args.query)
        if args.type == "txt":
            for i, lib in enumerate(result.get("results", []), 1):
                print(f"{i}. {lib.get('title', 'N/A')} ({lib.get('id', 'N/A')})")
                if lib.get("description"):
                    print(f"   {lib.get('description')}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "context":
        result = get_context(args.library_id, args.query, args.type)
        if args.type == "txt":
            print(result)  # type: ignore[arg-type]
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

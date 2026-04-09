#!/usr/bin/env python3
"""
Post due reels from publish_queue/ using the Meta Graph API.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


GRAPH_VERSION = "v19.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Post due reels from the publish queue.")
    parser.add_argument("--queue-dir", default="publish_queue", help="Queue directory to scan.")
    parser.add_argument(
        "--branch",
        default=os.environ.get("PUBLISH_BRANCH") or os.environ.get("GITHUB_REF_NAME") or "main",
        help="Git branch used to build raw GitHub URLs.",
    )
    return parser.parse_args()


def build_raw_video_url(repo_name: str, branch: str, video_path: str) -> str:
    quoted_path = quote(video_path.replace("\\", "/"), safe="/")
    return f"https://raw.githubusercontent.com/{repo_name}/{branch}/{quoted_path}"


def request_json(method: str, url: str, **kwargs) -> dict:
    response = requests.request(method, url, timeout=60, **kwargs)
    try:
        payload = response.json()
    except Exception:
        payload = {"raw_response": response.text}

    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code}: {payload}")
    return payload


def create_container(
    ig_user_id: str,
    access_token: str,
    video_url: str,
    caption: str,
    share_to_feed: bool,
    thumb_offset_ms: int,
) -> str:
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{ig_user_id}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": str(share_to_feed).lower(),
        "thumb_offset": int(thumb_offset_ms),
        "access_token": access_token,
    }
    response = request_json("POST", url, data=payload)
    container_id = response.get("id")
    if not container_id:
        raise RuntimeError(f"Container creation did not return an id: {response}")
    return container_id


def wait_for_container(container_id: str, access_token: str) -> None:
    status_url = (
        f"https://graph.facebook.com/{GRAPH_VERSION}/{container_id}"
        f"?fields=status_code&access_token={access_token}"
    )
    for _ in range(30):
        response = request_json("GET", status_url)
        status_code = response.get("status_code")
        if status_code == "FINISHED":
            return
        if status_code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Container failed with status {status_code}: {response}")
        time.sleep(10)
    raise RuntimeError("Timed out waiting for Meta to finish processing the reel.")


def publish_container(ig_user_id: str, access_token: str, container_id: str) -> str:
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{ig_user_id}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": access_token,
    }
    response = request_json("POST", url, data=payload)
    media_id = response.get("id")
    if not media_id:
        raise RuntimeError(f"Publish call did not return an id: {response}")
    return media_id


def load_due_manifests(queue_dir: Path) -> list[Path]:
    now_utc = datetime.now(timezone.utc)
    due: list[Path] = []

    for manifest_path in sorted(queue_dir.glob("*.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("posted"):
            continue
        scheduled_at = manifest.get("scheduled_at")
        if not scheduled_at:
            continue
        scheduled_dt = datetime.fromisoformat(scheduled_at)
        if scheduled_dt.astimezone(timezone.utc) <= now_utc:
            due.append(manifest_path)

    return due


def main() -> int:
    args = parse_args()
    queue_dir = Path(args.queue_dir)
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
    access_token = os.environ.get("META_ACCESS_TOKEN")
    max_posts_raw = os.environ.get("MAX_POSTS_PER_RUN")

    if not repo_name:
        raise SystemExit("GITHUB_REPOSITORY is required.")
    if not ig_user_id:
        raise SystemExit("INSTAGRAM_USER_ID is required.")
    if not access_token:
        raise SystemExit("META_ACCESS_TOKEN is required.")
    if not queue_dir.exists():
        print(f"[SKIP] Queue directory not found: {queue_dir}")
        return 0

    due_manifests = load_due_manifests(queue_dir)
    if max_posts_raw:
        due_manifests = due_manifests[: int(max_posts_raw)]

    if not due_manifests:
        print("[SKIP] No reels are due right now.")
        return 0

    failures = 0
    for manifest_path in due_manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        video_url = build_raw_video_url(repo_name, args.branch, manifest["video_path"])
        print(f"[POST] {manifest_path.name} -> {video_url}")

        manifest["last_attempt_at"] = datetime.now(timezone.utc).isoformat()

        try:
            container_id = create_container(
                ig_user_id=ig_user_id,
                access_token=access_token,
                video_url=video_url,
                caption=manifest.get("caption", ""),
                share_to_feed=bool(manifest.get("share_to_feed", True)),
                thumb_offset_ms=int(manifest.get("thumb_offset_ms", 0)),
            )
            wait_for_container(container_id, access_token)
            media_id = publish_container(ig_user_id, access_token, container_id)

            manifest["posted"] = True
            manifest["posted_at"] = datetime.now(timezone.utc).isoformat()
            manifest["instagram_media_id"] = media_id
            manifest["last_error"] = None
            print(f"[OK] Posted {manifest_path.name} as media {media_id}")
        except Exception as exc:
            failures += 1
            manifest["last_error"] = str(exc)
            print(f"[ERROR] {manifest_path.name}: {exc}")

        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

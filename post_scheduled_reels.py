#!/usr/bin/env python3
"""
Post reels from publish_queue/ using the Meta Graph API.

Instead of fixed scheduled_at timestamps, this script:
  1. Generates a fresh daily schedule with ONE random post time per slot window.
  2. On each run (every 30 min via cron), checks if NOW falls inside the
     ±15-minute match window of a pending slot.
  3. If a slot is due, picks a RANDOM unpublished reel and posts it.

Slot windows (Asia/Kolkata):
  Morning  : 07:30 – 09:00
  Lunch    : 12:30 – 14:00
  Evening  : 17:30 – 19:00
  Night    : 21:00 – 22:30
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests


GRAPH_VERSION = "v19.0"
IST = ZoneInfo("Asia/Kolkata")

# Slot definitions: (name, start_hour, start_min, end_hour, end_min)
POSTING_SLOTS = [
    ("morning", 7, 30, 9, 0),
    ("lunch", 12, 30, 14, 0),
    ("evening", 17, 30, 19, 0),
    ("night", 21, 0, 22, 30),
]

# A run is "on time" if it's within this many minutes of the chosen slot time
MATCH_WINDOW_MINUTES = 15


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Post reels from the publish queue.")
    parser.add_argument(
        "--queue-dir", default="publish_queue",
        help="Queue directory to scan (default: publish_queue).",
    )
    parser.add_argument(
        "--branch",
        default=os.environ.get("PUBLISH_BRANCH") or os.environ.get("GITHUB_REF_NAME") or "main",
        help="Git branch used to build raw GitHub URLs.",
    )
    return parser.parse_args()


# ── Meta Graph API helpers ────────────────────────────────────────────────────

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


# ── Daily schedule helpers ────────────────────────────────────────────────────

def _random_time_in_slot(
    sh: int, sm: int, eh: int, em: int, today_date, tz: ZoneInfo
) -> datetime:
    """Return a random datetime within [start, end) for today."""
    start = datetime(today_date.year, today_date.month, today_date.day, sh, sm, tzinfo=tz)
    end   = datetime(today_date.year, today_date.month, today_date.day, eh, em, tzinfo=tz)
    delta_secs = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta_secs))


def load_daily_schedule(schedule_path: Path, today_str: str) -> dict:
    """
    Load today's schedule from disk.
    If the file is missing or stale (different date), generate a fresh one.
    """
    if schedule_path.exists():
        try:
            data = json.loads(schedule_path.read_text(encoding="utf-8"))
            if data.get("date") == today_str:
                return data
        except Exception:
            pass  # corrupt file → regenerate

    today = datetime.now(IST).date()
    slots: dict[str, str] = {}
    for name, sh, sm, eh, em in POSTING_SLOTS:
        dt = _random_time_in_slot(sh, sm, eh, em, today, IST)
        slots[name] = dt.isoformat()

    schedule = {
        "date": today_str,
        "timezone": "Asia/Kolkata",
        "slots": slots,
        "posted_slots": [],
    }
    schedule_path.parent.mkdir(parents=True, exist_ok=True)
    schedule_path.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[SCHEDULE] Fresh daily schedule for {today_str}:")
    for name, iso_time in slots.items():
        local = datetime.fromisoformat(iso_time).strftime("%I:%M %p")
        print(f"  {name:<8} → {local}")

    return schedule


def find_due_slot(schedule: dict, now_ist: datetime) -> str | None:
    """
    Return the slot name if now_ist is within MATCH_WINDOW_MINUTES of its
    chosen post time AND it hasn't been posted today yet.
    """
    posted = set(schedule.get("posted_slots", []))
    window = timedelta(minutes=MATCH_WINDOW_MINUTES)

    for name, iso_time in schedule["slots"].items():
        if name in posted:
            continue
        slot_dt = datetime.fromisoformat(iso_time)
        if abs(now_ist - slot_dt) <= window:
            return name

    return None


# ── Queue helpers ─────────────────────────────────────────────────────────────

def pick_random_unpublished(queue_dir: Path) -> Path | None:
    """Return a random unpublished reel manifest, or None if queue is empty."""
    candidates: list[Path] = []
    for manifest_path in queue_dir.glob("*.json"):
        if manifest_path.name.startswith("."):
            continue  # skip hidden files like .daily_schedule.json
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not manifest.get("posted"):
                candidates.append(manifest_path)
        except Exception:
            continue

    if not candidates:
        return None
    return random.choice(candidates)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    args = parse_args()
    queue_dir    = Path(args.queue_dir)
    repo_name    = os.environ.get("GITHUB_REPOSITORY")
    ig_user_id   = os.environ.get("INSTAGRAM_USER_ID")
    access_token = os.environ.get("META_ACCESS_TOKEN")

    if not repo_name:
        raise SystemExit("GITHUB_REPOSITORY env var is required.")
    if not ig_user_id:
        raise SystemExit("INSTAGRAM_USER_ID env var is required.")
    if not access_token:
        raise SystemExit("META_ACCESS_TOKEN env var is required.")
    if not queue_dir.exists():
        print(f"[SKIP] Queue directory not found: {queue_dir}")
        return 0

    now_ist    = datetime.now(IST)
    today_str  = now_ist.strftime("%Y-%m-%d")
    print(f"[RUN] {now_ist.strftime('%Y-%m-%d %I:%M %p %Z')}")

    # 1. Load (or generate) today's random post schedule
    schedule_path = queue_dir / ".daily_schedule.json"
    schedule      = load_daily_schedule(schedule_path, today_str)

    # 2. Check if any slot is due right now
    due_slot = find_due_slot(schedule, now_ist)
    if not due_slot:
        print(f"[SKIP] No slot is due right now. Next check in 30 min.")
        return 0

    print(f"[SLOT] '{due_slot}' slot is due — picking a random reel...")

    # 3. Pick a random unpublished reel
    manifest_path = pick_random_unpublished(queue_dir)
    if not manifest_path:
        print("[SKIP] No unpublished reels left in queue.")
        # Mark slot done so we don't keep retrying an empty queue
        schedule["posted_slots"].append(due_slot)
        schedule_path.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
        return 0

    manifest  = json.loads(manifest_path.read_text(encoding="utf-8"))
    video_url = build_raw_video_url(repo_name, args.branch, manifest["video_path"])
    print(f"[POST] {manifest_path.name} → {video_url}")

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

        manifest["posted"]              = True
        manifest["posted_at"]           = datetime.now(timezone.utc).isoformat()
        manifest["instagram_media_id"]  = media_id
        manifest["last_error"]          = None
        print(f"[OK] Posted {manifest_path.name} → Instagram media {media_id}")

        # Mark this slot as done for today
        schedule["posted_slots"].append(due_slot)
        schedule_path.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")

    except Exception as exc:
        manifest["last_error"] = str(exc)
        print(f"[ERROR] {manifest_path.name}: {exc}")
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return 1

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

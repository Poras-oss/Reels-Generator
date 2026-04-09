#!/usr/bin/env python3
"""
Generate reels and prepare a Git-tracked publish queue.

Each queued reel is stored as:
  publish_queue/<same-stem>.mp4
  publish_queue/<same-stem>.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from Generate import ALL_CATEGORIES, ZODIAC_SIGNS


DEFAULT_QUEUE_DIR = Path("publish_queue")
DEFAULT_OUTPUT_DIR = Path("reels_output")
DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_SLOTS = "08:00,13:00,18:00,21:00"


@dataclass(frozen=True)
class ReelArtifact:
    sign: str
    category: str
    language: str
    video_path: Path
    script_path: Path

    @property
    def stem(self) -> str:
        return self.video_path.stem


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate reels and build same-name JSON manifests for GitHub Actions."
    )
    parser.add_argument(
        "--sign",
        choices=ZODIAC_SIGNS + ["all"],
        default="all",
        help="Zodiac sign to generate. Default: all",
    )
    parser.add_argument(
        "--category",
        choices=ALL_CATEGORIES + ["all", "horoscope"],
        default="horoscope",
        help="Category to generate. Default: horoscope",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Where Generate.py writes intermediate reel files.",
    )
    parser.add_argument(
        "--queue-dir",
        default=str(DEFAULT_QUEUE_DIR),
        help="Folder to commit and push. Each reel gets a same-stem JSON file here.",
    )
    parser.add_argument(
        "--timezone",
        default=DEFAULT_TIMEZONE,
        help=f"Scheduling timezone. Default: {DEFAULT_TIMEZONE}",
    )
    parser.add_argument(
        "--slots",
        default=DEFAULT_SLOTS,
        help=f"Daily posting slots, comma separated. Default: {DEFAULT_SLOTS}",
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help="Optional schedule start date in YYYY-MM-DD. If omitted, uses the next free slot.",
    )
    parser.add_argument(
        "--source-date",
        default=None,
        help="Optional reel file date in YYYYMMDD. Default: today in the selected timezone.",
    )
    parser.add_argument(
        "--soundtrack",
        default=None,
        help="Optional soundtrack path forwarded to Generate.py.",
    )
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Do not call Generate.py. Only build queue files from existing reel outputs.",
    )
    return parser.parse_args()


def expand_signs(sign_arg: str) -> list[str]:
    return ZODIAC_SIGNS if sign_arg == "all" else [sign_arg]


def expand_categories(category_arg: str) -> list[str]:
    if category_arg == "all":
        return list(ALL_CATEGORIES)
    return [category_arg]


def parse_slots(slot_string: str) -> list[time]:
    slots: list[time] = []
    for raw in slot_string.split(","):
        value = raw.strip()
        if not value:
            continue
        hour_str, minute_str = value.split(":", 1)
        slots.append(time(hour=int(hour_str), minute=int(minute_str)))
    if not slots:
        raise ValueError("At least one schedule slot is required.")
    return sorted(slots)


def resolve_source_date(source_date: str | None, tz_name: str) -> str:
    if source_date:
        datetime.strptime(source_date, "%Y%m%d")
        return source_date
    return datetime.now(ZoneInfo(tz_name)).strftime("%Y%m%d")


def build_generation_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "Generate.py",
        "--sign",
        args.sign,
        "--category",
        args.category,
        "--output",
        args.output,
    ]
    if args.soundtrack:
        command.extend(["--soundtrack", args.soundtrack])
    return command


def expected_artifacts(
    output_dir: Path,
    signs: Iterable[str],
    categories: Iterable[str],
    source_date: str,
) -> list[ReelArtifact]:
    artifacts: list[ReelArtifact] = []
    for category in categories:
        for sign in signs:
            sign_slug = sign.lower()
            if category == "horoscope":
                artifacts.append(
                    ReelArtifact(
                        sign=sign,
                        category=category,
                        language="en",
                        video_path=output_dir / f"{sign_slug}_{source_date}_reel.mp4",
                        script_path=output_dir / f"{sign_slug}_{source_date}_script.json",
                    )
                )
                continue

            for language in ("en", "hi"):
                artifacts.append(
                    ReelArtifact(
                        sign=sign,
                        category=category,
                        language=language,
                        video_path=output_dir / f"{sign_slug}_{category}_{source_date}_{language}_reel.mp4",
                        script_path=output_dir / f"{sign_slug}_{category}_{source_date}_{language}_script.json",
                    )
                )
    return artifacts


def load_existing_pending_cutoff(queue_dir: Path, fallback_dt: datetime) -> datetime:
    latest = fallback_dt
    if not queue_dir.exists():
        return latest

    for manifest_path in sorted(queue_dir.glob("*.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("posted"):
                continue
            scheduled_at = manifest.get("scheduled_at")
            if not scheduled_at:
                continue
            scheduled_dt = datetime.fromisoformat(scheduled_at)
            if scheduled_dt > latest:
                latest = scheduled_dt
        except Exception:
            continue
    return latest


def next_schedule_times(
    count: int,
    tz_name: str,
    slot_times: list[time],
    queue_dir: Path,
    start_date_arg: str | None,
) -> list[datetime]:
    tz = ZoneInfo(tz_name)
    now_local = datetime.now(tz)

    if start_date_arg:
        start_day = date.fromisoformat(start_date_arg)
        cursor = datetime.combine(start_day, time(0, 0), tzinfo=tz) - timedelta(seconds=1)
    else:
        cursor = load_existing_pending_cutoff(queue_dir, now_local)

    scheduled: list[datetime] = []
    current_day = cursor.date()

    while len(scheduled) < count:
        for slot in slot_times:
            candidate = datetime.combine(current_day, slot, tzinfo=tz)
            if candidate <= cursor:
                continue
            scheduled.append(candidate)
            if len(scheduled) == count:
                break
        current_day += timedelta(days=1)

    return scheduled


def build_caption(script: dict, sign: str, category: str, language: str) -> str:
    lines: list[str] = []

    hook = str(script.get("hook", "")).strip()
    if hook:
        lines.append(hook)

    body_lines = [str(line).strip() for line in script.get("body", []) if str(line).strip()]
    if body_lines:
        lines.append("\n".join(body_lines[:4]))

    reveal = str(script.get("reveal", "")).strip()
    if reveal:
        lines.append(reveal)

    stats: list[str] = []
    if script.get("lucky_number") not in (None, ""):
        stats.append(f"Lucky number: {script['lucky_number']}")
    if script.get("lucky_color"):
        stats.append(f"Lucky color: {script['lucky_color']}")
    if script.get("vibe_word"):
        stats.append(f"Today's vibe: {script['vibe_word']}")
    if stats:
        lines.append("\n".join(stats))

    cta = str(script.get("cta", "")).strip()
    if cta:
        lines.append(cta)

    hashtags = [
        "#horoscope",
        "#astrology",
        "#dailyhoroscope",
        f"#{sign.lower()}",
        "#zodiac",
        "#reels",
    ]
    if category != "horoscope":
        hashtags.append(f"#{category.replace('_', '')}")
    if language == "hi":
        hashtags.append("#hindi")

    lines.append(" ".join(hashtags))
    return "\n\n".join(part for part in lines if part).strip()


def ensure_not_overwriting_posted_manifest(manifest_path: Path) -> None:
    if not manifest_path.exists():
        return
    existing = json.loads(manifest_path.read_text(encoding="utf-8"))
    if existing.get("posted"):
        raise RuntimeError(
            f"Refusing to overwrite already-posted queue item: {manifest_path}"
        )


def write_queue_item(
    artifact: ReelArtifact,
    script: dict,
    scheduled_at: datetime,
    queue_dir: Path,
) -> Path:
    queue_dir.mkdir(parents=True, exist_ok=True)

    destination_video = queue_dir / artifact.video_path.name
    destination_manifest = queue_dir / f"{artifact.stem}.json"
    ensure_not_overwriting_posted_manifest(destination_manifest)

    shutil.copy2(artifact.video_path, destination_video)

    manifest = {
        "version": 1,
        "sign": artifact.sign,
        "category": artifact.category,
        "language": artifact.language,
        "video_filename": destination_video.name,
        "video_path": destination_video.as_posix(),
        "scheduled_at": scheduled_at.isoformat(),
        "scheduled_timezone": str(scheduled_at.tzinfo),
        "share_to_feed": True,
        "thumb_offset_ms": 0,
        "posted": False,
        "posted_at": None,
        "instagram_media_id": None,
        "last_error": None,
        "caption": build_caption(script, artifact.sign, artifact.category, artifact.language),
        "script": script,
        "created_at": datetime.now(tz=ZoneInfo("UTC")).isoformat(),
    }

    destination_manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return destination_manifest


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output)
    queue_dir = Path(args.queue_dir)
    signs = expand_signs(args.sign)
    categories = expand_categories(args.category)
    source_date = resolve_source_date(args.source_date, args.timezone)

    if not args.skip_generate:
        command = build_generation_command(args)
        print(f"[RUN] {' '.join(command)}")
        subprocess.run(command, check=True)

    artifacts = expected_artifacts(output_dir, signs, categories, source_date)
    missing: list[str] = []
    available: list[ReelArtifact] = []

    for artifact in artifacts:
        if artifact.video_path.exists() and artifact.script_path.exists():
            available.append(artifact)
        else:
            if not artifact.video_path.exists():
                missing.append(str(artifact.video_path))
            if not artifact.script_path.exists():
                missing.append(str(artifact.script_path))

    if missing:
        missing_text = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(f"Expected generated files were not found:\n{missing_text}")

    schedules = next_schedule_times(
        count=len(available),
        tz_name=args.timezone,
        slot_times=parse_slots(args.slots),
        queue_dir=queue_dir,
        start_date_arg=args.start_date,
    )

    print(f"[QUEUE] Writing {len(available)} reel manifests to {queue_dir}")
    for artifact, scheduled_at in zip(available, schedules):
        script = json.loads(artifact.script_path.read_text(encoding="utf-8"))
        manifest_path = write_queue_item(artifact, script, scheduled_at, queue_dir)
        print(
            f"  - {artifact.video_path.name} -> {manifest_path.name} "
            f"({scheduled_at.strftime('%Y-%m-%d %H:%M %Z')})"
        )

    print("\n[NEXT] Commit and push the publish_queue folder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

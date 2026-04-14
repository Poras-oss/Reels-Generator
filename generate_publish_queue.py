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
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from Generate import ALL_CATEGORIES, ZODIAC_SIGNS
from fun_genre_categories import FUN_GENRES, get_all_subjects


DEFAULT_QUEUE_DIR = Path("publish_queue")
DEFAULT_OUTPUT_DIR = Path("reels_output")
DEFAULT_TIMEZONE = "Asia/Kolkata"


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
        help=f"Timezone for naming source-date files. Default: {DEFAULT_TIMEZONE}",
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
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Forward --parallel flag to Generate.py",
    )
    parser.add_argument(
        "--genre",
        choices=FUN_GENRES + ["all"],
        default=None,
        help="Fun genre to generate. If set, --sign and --category are ignored.",
    )
    parser.add_argument(
        "--subject",
        default="all",
        help="Subject slug within the genre, or 'all' (default: all).",
    )
    return parser.parse_args()


def expand_signs(sign_arg: str) -> list[str]:
    return ZODIAC_SIGNS if sign_arg == "all" else [sign_arg]


def expand_categories(category_arg: str) -> list[str]:
    if category_arg == "all":
        return list(ALL_CATEGORIES)
    return [category_arg]



def resolve_source_date(source_date: str | None, tz_name: str) -> str:
    if source_date:
        datetime.strptime(source_date, "%Y%m%d")
        return source_date
    return datetime.now(ZoneInfo(tz_name)).strftime("%Y%m%d")


def build_generation_command(args: argparse.Namespace) -> list[str]:
    # Fun genre path
    if getattr(args, "genre", None):
        command = [
            sys.executable, "Generate.py",
            "--genre", args.genre,
            "--subject", args.subject,
            "--output", args.output,
        ]
    else:
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
    if args.parallel:
        command.append("--parallel")
    return command


def expected_artifacts(
    output_dir: Path,
    signs: Iterable[str],
    categories: Iterable[str],
    source_date: str,
    genre: str | None = None,
    subject: str = "all",
) -> list[ReelArtifact]:
    artifacts: list[ReelArtifact] = []

    # ── Fun genre reels ──────────────────────────────────────────────────────
    if genre:
        genres = FUN_GENRES if genre == "all" else [genre]
        for g in genres:
            subjects = get_all_subjects(g)
            if subject != "all":
                subjects = [s for s in subjects if s[0].lower() == subject.lower()]
            for slug, label, extra in subjects:
                file_slug = f"{slug.lower()}_{g}_{source_date}"
                artifacts.append(
                    ReelArtifact(
                        sign=extra.get("sign", slug),
                        category=g,
                        language="en",
                        video_path=output_dir / f"{file_slug}_en_reel.mp4",
                        script_path=output_dir / f"{file_slug}_en_script.json",
                    )
                )
        return artifacts

    # ── Classic sign / category reels ────────────────────────────────────────
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

            for language in ("en",):
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



def build_caption(script: dict, sign: str, category: str, language: str) -> str:
    lines: list[str] = []

    hook = str(script.get("hook", "")).strip()
    if hook:
        lines.append(hook)

    # Fun genre — use insights instead of body
    genre = script.get("genre")
    if genre:
        insights = [str(i).strip() for i in script.get("insights", []) if str(i).strip()]
        if insights:
            lines.append("\n".join(insights[:3]))

        # Genre-specific extras in caption
        for key in ("personality_trait", "power_period", "cosmic_message",
                    "chemistry", "verdict", "compatibility_score"):
            val = str(script.get(key, "")).strip()
            if val:
                lines.append(val)
                break  # just the first one
    else:
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

    music_credit = str(script.get("soundtrack_credit", "")).strip()
    if music_credit:
        lines.append(music_credit)

    subject = str(script.get("subject", "")).strip()
    if genre:
        hashtags = [
            f"#{genre.replace('_', '')}",
            "#astrology",
            "#zodiac",
            "#cosmic",
        ]
        if subject:
            safe = subject.replace(" ", "").replace("&", "").replace("-", "").lower()
            hashtags.append(f"#{safe}")
    else:
        hashtags = [
            f"#{sign.lower()}",
            "#astrology",
            "#horoscope",
        ]
        if category != "horoscope":
            hashtags.append(f"#{category.replace('_', '')}")
        else:
            hashtags.append("#dailyhoroscope")
        if language == "hi":
            hashtags.append("#jyotish")

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
        "share_to_feed": True,
        "thumb_offset_ms": 4000,
        "posted": False,
        "posted_at": None,
        "instagram_media_id": None,
        "last_error": None,
        "caption": build_caption(script, artifact.sign, artifact.category, artifact.language),
        "script": script,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    destination_manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return destination_manifest


def main() -> int:
    args = parse_args()
    output_dir  = Path(args.output)
    queue_dir   = Path(args.queue_dir)
    source_date = resolve_source_date(args.source_date, args.timezone)
    genre       = getattr(args, "genre", None)
    subject     = getattr(args, "subject", "all")

    # For classic path, expand signs/categories
    signs      = expand_signs(args.sign) if not genre else []
    categories = expand_categories(args.category) if not genre else []

    if not args.skip_generate:
        command = build_generation_command(args)
        print(f"[RUN] {' '.join(command)}")
        subprocess.run(command, check=True)

    artifacts = expected_artifacts(
        output_dir, signs, categories, source_date,
        genre=genre, subject=subject,
    )
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

    print(f"[QUEUE] Writing {len(available)} reel manifests to {queue_dir}")
    for artifact in available:
        script = json.loads(artifact.script_path.read_text(encoding="utf-8"))
        manifest_path = write_queue_item(artifact, script, queue_dir)
        print(f"  - {artifact.video_path.name} -> {manifest_path.name}")

    print("\n[NEXT] Commit and push the publish_queue folder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

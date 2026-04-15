# Reel Posting Algorithm

This project posts Instagram reels from the Git-tracked `publish_queue/` folder using GitHub Actions and the Meta Graph API.

## Files Involved

- `.github/workflows/post-scheduled-reels.yml`
- `post_scheduled_reels.py`
- `generate_publish_queue.py`
- `publish_queue/*.json`
- `publish_queue/*.mp4`
- `publish_queue/.daily_schedule.json`

## High-Level Flow

1. `generate_publish_queue.py` creates queue items.
2. Each reel gets:
   - one video file: `publish_queue/<name>.mp4`
   - one manifest file: `publish_queue/<name>.json`
3. GitHub Actions runs `post_scheduled_reels.py` every 30 minutes.
4. The posting script creates or loads today's random posting schedule.
5. If the current IST time matches a due slot, the script picks one random unpublished reel.
6. It uploads and publishes that reel through the Meta Graph API.
7. The manifest is updated with posting status.
8. The workflow commits queue changes back to the repo.

## Queue Item Format

Each manifest in `publish_queue/*.json` stores:

- `video_path`
- `caption`
- `posted`
- `posted_at`
- `instagram_media_id`
- `last_error`
- `last_attempt_at`

The reel is considered available for posting when:

- `posted` is `false`

## Daily Scheduling Logic

The script does not use a fixed `scheduled_at` timestamp anymore.

Instead, every day it creates one random post time inside each of these IST slot windows:

- Morning: `07:30` to `09:00`
- Lunch: `12:30` to `14:00`
- Evening: `17:30` to `19:00`
- Night: `21:00` to `22:30`

That data is stored in:

- `publish_queue/.daily_schedule.json`

The file contains:

- `date`
- `timezone`
- `slots`
- `posted_slots`

Example idea:

```json
{
  "date": "2026-04-15",
  "timezone": "Asia/Kolkata",
  "slots": {
    "morning": "2026-04-15T08:11:23+05:30",
    "lunch": "2026-04-15T13:07:10+05:30"
  },
  "posted_slots": ["morning"]
}
```

## How a Reel Gets Picked

On each workflow run:

1. The script loads `publish_queue/.daily_schedule.json`.
2. If the file is missing or from a different date, it creates a fresh schedule for today.
3. It checks whether the current IST time is within `±15 minutes` of any unposted slot.
4. If no slot is due, it exits without posting.
5. If a slot is due, it scans `publish_queue/*.json`.
6. It ignores hidden files like `.daily_schedule.json`.
7. It collects manifests where `posted` is `false`.
8. It picks one random unpublished reel.

## Posting Logic

When a reel is due:

1. Build a raw GitHub URL for the MP4 using:
   - repo name
   - branch name
   - `video_path`
2. Create an Instagram reel container through the Meta Graph API.
3. Wait for processing to finish.
4. Publish the container.
5. Update the manifest:
   - `posted = true`
   - `posted_at = <utc timestamp>`
   - `instagram_media_id = <returned media id>`
   - `last_error = null`
6. Mark the slot in `.daily_schedule.json` as completed by appending to `posted_slots`.

If posting fails:

- `last_attempt_at` is updated
- `last_error` is saved
- the script exits with a non-zero code

## GitHub Actions Behavior

The workflow:

1. Checks out the repo
2. Sets up Python
3. Installs `requests`
4. Runs `post_scheduled_reels.py --queue-dir publish_queue`
5. Commits updated queue files back to GitHub

The important part is that the workflow must commit:

- changed manifest files
- newly created `.daily_schedule.json`

## Important Bug To Remember

After the "act more human" change, posting started depending on `publish_queue/.daily_schedule.json`.

If GitHub Actions does not commit that file, every scheduled run creates a brand new random schedule. That means the chosen slot times keep resetting, and reels may never post because the workflow keeps missing its own moving target.

The fix in `.github/workflows/post-scheduled-reels.yml` is:

```yaml
git add -A publish_queue
if git diff --cached --quiet; then
  echo "No queue changes to commit."
  exit 0
fi
git commit -m "chore: update reel publish queue"
git push
```

This matters because:

- `git diff --quiet -- publish_queue` does not notice untracked files
- `.daily_schedule.json` is often created as a new file
- staging first ensures the workflow sees and commits it

## Mental Model

Think of the system like this:

- `generate_publish_queue.py` prepares inventory
- `post_scheduled_reels.py` decides when to post and what to post
- `.daily_schedule.json` remembers today's random timing
- GitHub Actions is the clock that wakes the script up every 30 minutes

If the daily schedule is not persisted, the clock still runs, but the plan for the day keeps getting rewritten.

## Future Debug Checklist

If reels stop posting again, check these first:

1. GitHub Actions is still running on schedule.
2. `.daily_schedule.json` is being committed to the repo.
3. Queue manifests still have `posted: false` items.
4. `INSTAGRAM_USER_ID` and `META_ACCESS_TOKEN` secrets are valid.
5. `PUBLISH_BRANCH` points to the branch where queue files exist.
6. Raw GitHub URLs for queued MP4 files are reachable.
7. Recent queue manifests contain `last_error` messages.


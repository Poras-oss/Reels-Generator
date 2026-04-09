# Auto Post Setup

This project now supports a queue-based workflow:

1. Run one command to generate reels.
2. Commit and push the `publish_queue/` folder.
3. GitHub Actions posts every reel whose JSON says `posted=false` and whose `scheduled_at` time has arrived.

## Local command

Use the new batch file:

```bat
generate_publish_queue.bat
```

Or directly:

```powershell
python generate_publish_queue.py --sign all --category horoscope
```

That creates files like:

```text
publish_queue/
  aries_20260409_reel.mp4
  aries_20260409_reel.json
  taurus_20260409_reel.mp4
  taurus_20260409_reel.json
```

Each JSON file contains:

- `scheduled_at`
- `posted`
- `caption`
- the full generated script

## Important requirement

Your GitHub repository must be public, because Meta needs a public video URL and the workflow uses `raw.githubusercontent.com/...` for the reel file.

## GitHub Secrets

Add these repository secrets:

- `INSTAGRAM_USER_ID`
- `META_ACCESS_TOKEN`

Optional secrets:

- `PUBLISH_BRANCH`
- `MAX_POSTS_PER_RUN`

## Schedule behavior

Default slots:

- `08:00`
- `13:00`
- `18:00`
- `21:00`

Default timezone: `Asia/Kolkata`

If there are already unposted items in `publish_queue/`, newly generated reels are scheduled after the last pending one.

## Manual trigger

You can also run the workflow manually from GitHub:

`Actions -> Post Scheduled Reels -> Run workflow`

## Notes

- The workflow runs every 15 minutes.
- After a successful post, the matching JSON is updated to `posted: true` and pushed back to the repo.
- If a post fails, the JSON keeps `posted: false` and stores the error in `last_error`.

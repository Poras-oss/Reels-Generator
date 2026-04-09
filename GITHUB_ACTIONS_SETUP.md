# GitHub Actions Setup

This file explains exactly what you need to configure on GitHub for automatic reel posting.

## What you need to do

Pushing the project files is necessary, but not sufficient by itself.

You must also configure a few things on GitHub:

1. Push this repository to GitHub.
2. Make sure GitHub Actions is enabled.
3. Add the required repository secrets.
4. Keep the repository public so Meta can fetch the reel video files from GitHub.

## Files that must be pushed

Make sure these are included in your push:

- `.github/workflows/post-scheduled-reels.yml`
- `post_scheduled_reels.py`
- `generate_publish_queue.py`
- `generate_publish_queue.bat`
- `publish_queue/`

## Required GitHub secrets

Go to:

`GitHub repo -> Settings -> Secrets and variables -> Actions`

Create these repository secrets:

### `INSTAGRAM_USER_ID`

Your Instagram Business account user id used by the Meta Graph API.

### `META_ACCESS_TOKEN`

Your long-lived Meta access token with the permissions needed to publish reels.

## Optional GitHub secrets

These are optional, but useful:

### `PUBLISH_BRANCH`

Example:

`main`

Use this if you always want the workflow to build raw GitHub video URLs from a fixed branch.

### `MAX_POSTS_PER_RUN`

Example:

`1`

Use this if you want to limit how many reels can be posted in one workflow execution.

## Repository visibility

Your repository should be **public**.

Reason:

The workflow sends Meta a video URL like:

`https://raw.githubusercontent.com/<owner>/<repo>/<branch>/publish_queue/file.mp4`

Meta must be able to access that URL publicly to fetch the reel video.

## Enable GitHub Actions

In your GitHub repository:

1. Open the `Actions` tab.
2. If GitHub asks whether to enable workflows, enable them.
3. After your first push, you should see the workflow:

`Post Scheduled Reels`

## Recommended first-time test

After pushing:

1. Open `Actions`
2. Open `Post Scheduled Reels`
3. Click `Run workflow`

This lets you test the workflow manually before waiting for the schedule.

## Your normal workflow after setup

Once GitHub is configured, your daily flow becomes:

1. Run:

```bat
generate_publish_queue.bat
```

2. Commit the generated `publish_queue/` files.
3. Push to GitHub.
4. GitHub Actions will automatically post reels when their JSON file has:

- `posted: false`
- `scheduled_at` time reached

## Notes

- The workflow runs every 15 minutes.
- After successful posting, the matching JSON file is updated to `posted: true`.
- If posting fails, the JSON file stays `posted: false` and `last_error` is filled in.

## Summary

Yes, you should push everything from here.

But before auto-posting works, you still need to do these GitHub configurations:

- add `INSTAGRAM_USER_ID`
- add `META_ACCESS_TOKEN`
- make sure Actions are enabled
- keep the repo public

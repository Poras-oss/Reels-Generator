# Process for Publishing Instagram Reels via Meta Graph API

This document outlines the step-by-step process of using the Meta Graph API to programmatically publish Reels to an Instagram account.

## Prerequisites
Before you begin, ensure you have the following:

- **Instagram Professional Account**: Your account must be a **Business** account (Creator accounts are not supported for content publishing via the API).
- **Linked Facebook Page**: The Instagram Business account must be linked to a Facebook Page.
- **Meta Developer App**: You need a Meta App configured with `instagram_business_basic` and `instagram_business_content_publish` permissions.
- **Access Tokens**: A valid Page Access Token with the necessary permissions.
- **Media Hosting**: The video file you want to upload must be hosted on a **publicly accessible URL** because Meta's servers will fetch the file from this URL. If using local files, you need to use the resumable upload API instead.

---

## Step-by-Step Publishing Process

The publishing process follows an asynchronous container-based workflow: creating a container, polling for its processing status, and finally publishing it.

### Step 1: Create a Media Container

First, you need to create a media container. This signals the Meta API to fetch your video from the provided URL.

**Endpoint:**
```http
POST https://graph.facebook.com/v19.0/{ig-user-id}/media
```

**Parameters:**
- `media_type` (Required): Must be set to `REELS`.
- `video_url` (Required): The publicly accessible URL of your video.
- `access_token` (Required): Your Page Access Token.
- `caption` (Optional): The text description and hashtags for your Reel.
- `share_to_feed` (Optional): `true` to show in both Grid & Reels tab, `false` for Reels tab only.
- `thumb_offset` (Optional): Time in milliseconds to use as the cover image.

**Response:**
If successful, this request will return an `id` (often referred to as an `ig-container-id` or `creation_id`). Save this ID for the next steps.

---

### Step 2: Poll for Processing Status

Once the container is created, Meta downloads and processes the video. This takes time depending on the video's size. You **must** wait until processing is completed; attempting to publish early will result in a 400 error.

**Endpoint:**
```http
GET https://graph.facebook.com/v19.0/{ig-container-id}?fields=status_code&access_token={your-token}
```

**Polling Logic:**
Ping this endpoint repeatedly (e.g., every 5-10 seconds) and check the `status_code` field. You can proceed to the next step once `status_code` equals `FINISHED`. 
*(Other statuses include `IN_PROGRESS`, `EXPIRED`, or `ERROR`.)*

---

### Step 3: Publish the Reel Container

Once the container status is `FINISHED`, you can officially publish the Reel to the Instagram account.

**Endpoint:**
```http
POST https://graph.facebook.com/v19.0/{ig-user-id}/media_publish
```

**Parameters:**
- `creation_id` (Required): The `ig-container-id` you obtained in Step 1.
- `access_token` (Required): Your Page Access Token.

**Response:**
Upon success, the API will return a final `id`. This is the Media ID of the newly published Instagram Reel post.

---

## Video Specifications & Limitations
- **Format:** MP4 or MOV.
- **Aspect Ratio:** 9:16 is strictly recommended.
- **Duration:** Between 3 seconds and 15 minutes (though it's recommended to keep it under 90 seconds to be eligible for the main algorithmic Reels tab).
- **Rate Limits:** Meta enforces a limit—usually 50 posts per 24-hour window per Instagram account.

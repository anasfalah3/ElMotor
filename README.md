# Facebook Motorcycle Page — Daily Auto-Poster (Darija)

Posts one motorcycle-themed caption (Darija) + a matching photo to your Facebook Page, 3 times a day, for free, using GitHub Actions.

## Files
- `captions.json` — the caption bank. Add, remove, or edit lines anytime (keep the JSON format: `text` + `search_term`).
- `post_to_facebook.py` — picks a random caption, fetches a matching photo from Pexels (if configured), and posts to your Page.
- `requirements.txt` — Python dependencies.
- `.github/workflows/daily-post.yml` — the schedule that runs the script 3 times a day.

## Setup

### 1. Create a Facebook App
Go to [developers.facebook.com](https://developers.facebook.com) → My Apps → Create App → "Other" → "Business".

### 2. Get a long-lived Page Access Token
1. Open [Graph API Explorer](https://developers.facebook.com/tools/explorer).
2. Select your app, click "Generate Access Token", and grant `pages_manage_posts` + `pages_read_engagement` permissions.
3. Exchange the short-lived user token for a long-lived one (Graph API Explorer has a button for this, or use the `oauth/access_token` endpoint with `grant_type=fb_exchange_token`).
4. Call `GET /me/accounts` with that long-lived user token — this returns your Pages along with a **Page access token** for each. That Page token is what you'll use; it typically doesn't expire as long as the user token behind it stays valid.

### 3. Find your Page ID
It's in the same `/me/accounts` response, or under your Page's About section.

### 4. (Optional but recommended) Get a free Pexels API key
Sign up at [pexels.com/api](https://www.pexels.com/api/) — instant, free. Without this key, posts will be text-only (still works fine).

### 5. Push these files to a new GitHub repo
Create a repo, upload all the files in this folder (keep the `.github/workflows/` structure intact).

### 6. Add your secrets
In the repo: **Settings → Secrets and variables → Actions → New repository secret**. Add:
- `FB_PAGE_ID`
- `FB_PAGE_ACCESS_TOKEN`
- `PEXELS_API_KEY` (optional)

### 7. Test it
Go to the **Actions** tab → "Daily Facebook Post" → "Run workflow" to trigger it manually and confirm it posts correctly before waiting for the schedule.

## Adjusting the schedule
Edit the `cron` lines in `.github/workflows/daily-post.yml`. Cron times are in UTC — Morocco is UTC+0 year-round (no DST since 2018, aside from a brief Ramadan shift some years).

## Adding more content
Just add more objects to `captions.json` in the same `{"text": "...", "search_term": "..."}` format. The `search_term` should be in English — it's used to search Pexels for a matching photo.

## Notes
- Page access tokens can occasionally need refreshing if permissions or the underlying user token change — if posts start failing with an auth error, regenerate the token via steps 2–3.
- Facebook API changes periodically; if `graph.facebook.com` calls start failing, check the current Graph API version at [developers.facebook.com/docs/graph-api/changelog](https://developers.facebook.com/docs/graph-api/changelog) and update `GRAPH_API_VERSION` in `post_to_facebook.py`.

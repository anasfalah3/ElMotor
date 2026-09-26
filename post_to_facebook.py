"""
Daily auto-poster for a Facebook Page about motorcycles (Darija captions).

Reads secrets from environment variables:
  FB_PAGE_ID            - your Facebook Page ID (required)
  FB_PAGE_ACCESS_TOKEN  - a long-lived Page access token (required)
  PEXELS_API_KEY        - free Pexels API key (optional; if missing, posts text-only)

Picks a random caption from captions.json, tries to find a matching photo
via the Pexels API, then posts to the Page via the Graph API.
"""

import json
import os
import random
import sys
import requests

GRAPH_API_VERSION = "v19.0"
CAPTIONS_FILE = os.path.join(os.path.dirname(__file__), "captions.json")


def load_random_caption():
    with open(CAPTIONS_FILE, "r", encoding="utf-8") as f:
        captions = json.load(f)
    if not captions:
        raise ValueError("captions.json is empty")
    return random.choice(captions)


def fetch_photo_url(search_term, pexels_api_key):
    """Return a photo URL from Pexels matching search_term, or None."""
    if not pexels_api_key:
        return None
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": pexels_api_key},
            params={"query": search_term, "per_page": 15, "orientation": "landscape"},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        photos = data.get("photos", [])
        if not photos:
            return None
        photo = random.choice(photos)
        return photo["src"]["large"]
    except requests.RequestException as e:
        print(f"Warning: Pexels fetch failed ({e}); falling back to text-only post.")
        return None


def post_to_facebook(page_id, access_token, message, photo_url=None):
    if photo_url:
        endpoint = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/photos"
        payload = {"url": photo_url, "caption": message, "access_token": access_token}
    else:
        endpoint = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/feed"
        payload = {"message": message, "access_token": access_token}

    resp = requests.post(endpoint, data=payload, timeout=30)
    if resp.status_code != 200:
        print(f"Facebook API error ({resp.status_code}): {resp.text}")
        resp.raise_for_status()
    return resp.json()


def main():
    page_id = os.environ.get("FB_PAGE_ID")
    access_token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
    pexels_api_key = os.environ.get("PEXELS_API_KEY")  # optional

    if not page_id or not access_token:
        print("Error: FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN must be set as environment variables / secrets.")
        sys.exit(1)

    caption = load_random_caption()
    photo_url = fetch_photo_url(caption["search_term"], pexels_api_key)

    result = post_to_facebook(page_id, access_token, caption["text"], photo_url)
    print("Posted successfully:", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

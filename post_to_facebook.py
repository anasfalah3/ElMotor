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


def resolve_page_token(page_id, access_token):
    """Return a Page access token for page_id.

    Posting to a Page with a *user* token fails with a misleading
    "(#200) publish_actions ... deprecated" error. If the given token turns out
    to be a user token, exchange it for the Page token via GET /{page_id}.
    """
    base = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
    resp = requests.get(f"{base}/me", params={"fields": "id", "access_token": access_token}, timeout=20)
    if resp.status_code != 200:
        print(f"Facebook API error checking token ({resp.status_code}): {resp.text}")
        resp.raise_for_status()
    if resp.json().get("id") == str(page_id):
        return access_token  # already a Page token

    print(
        "Warning: FB_PAGE_ACCESS_TOKEN is a USER token, not a Page token. "
        "Trying to fetch the Page token from it. Replace the secret with the Page "
        "token from GET /me/accounts (see README step 2)."
    )
    resp = requests.get(
        f"{base}/{page_id}", params={"fields": "access_token", "access_token": access_token}, timeout=20
    )
    page_token = resp.json().get("access_token") if resp.status_code == 200 else None
    if not page_token:
        print(
            f"Error: could not get a Page token for page {page_id} ({resp.status_code}): {resp.text}\n"
            "Make sure the user token has pages_manage_posts + pages_read_engagement "
            "(and pages_show_list), and that you are an admin of this Page."
        )
        sys.exit(1)
    return page_token


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

    access_token = resolve_page_token(page_id, access_token)

    caption = load_random_caption()
    photo_url = fetch_photo_url(caption["search_term"], pexels_api_key)

    result = post_to_facebook(page_id, access_token, caption["text"], photo_url)
    print("Posted successfully:", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

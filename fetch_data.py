"""Fetch public GitHub repositories and load raw + cleaned records into SQLite."""
import json, os, sqlite3, time
from datetime import datetime, timezone
import requests
from requests.exceptions import RequestException

DB_PATH = os.getenv("DB_PATH", "github_analytics.db")
API_URL = "https://api.github.com/search/repositories"
SEARCH_QUERY = os.getenv("GITHUB_QUERY", "stars:>1000")
MAX_PAGES = int(os.getenv("MAX_PAGES", "3"))  # Keep the demo small and rate-limit friendly.
PER_PAGE = 100

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_api_responses (
  response_id INTEGER PRIMARY KEY AUTOINCREMENT,
  fetched_at TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  page_number INTEGER NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS repositories (
  repo_id INTEGER PRIMARY KEY,
  full_name TEXT NOT NULL,
  owner_login TEXT,
  description TEXT,
  language TEXT NOT NULL DEFAULT 'Unknown',
  stars INTEGER NOT NULL DEFAULT 0,
  forks INTEGER NOT NULL DEFAULT 0,
  open_issues INTEGER NOT NULL DEFAULT 0,
  created_at TEXT,
  updated_at TEXT,
  html_url TEXT,
  fetched_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_repositories_language ON repositories(language);
"""

def as_nonnegative_int(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0

def main():
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "github-repo-analytics-demo"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    total = 0
    try:
        with requests.Session() as session:
            for page in range(1, MAX_PAGES + 1):
                params = {"q": SEARCH_QUERY, "sort": "stars", "order": "desc", "per_page": PER_PAGE, "page": page}
                response = None
                for attempt in range(3):
                    try:
                        response = session.get(API_URL, headers=headers, params=params, timeout=30)
                        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                            reset = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                            wait_seconds = max(1, min(reset - int(time.time()) + 1, 60))
                            print(f"Rate limit reached; waiting {wait_seconds}s (max 60s in this demo).")
                            time.sleep(wait_seconds)
                            continue
                        response.raise_for_status()
                        break
                    except RequestException as exc:
                        if attempt == 2:
                            raise RuntimeError(f"GitHub API request failed after 3 attempts: {exc}") from exc
                        time.sleep(2 ** attempt)
                if response is None or not response.ok:
                    raise RuntimeError("Could not retrieve a successful response from GitHub.")
                payload = response.json()
                items = payload.get("items") or []
                conn.execute(
                    "INSERT INTO raw_api_responses (fetched_at, endpoint, page_number, payload_json) VALUES (?, ?, ?, ?)",
                    (fetched_at, response.url, page, json.dumps(payload))
                )
                for item in items:
                    repo_id = item.get("id")
                    full_name = item.get("full_name")
                    if repo_id is None or not full_name:
                        print("Skipping malformed repository record: missing id/full_name")
                        continue
                    owner = item.get("owner") or {}
                    values = (
                        repo_id, full_name, owner.get("login"), item.get("description"),
                        item.get("language") or "Unknown", as_nonnegative_int(item.get("stargazers_count")),
                        as_nonnegative_int(item.get("forks_count")), as_nonnegative_int(item.get("open_issues_count")),
                        item.get("created_at"), item.get("updated_at"), item.get("html_url"), fetched_at
                    )
                    conn.execute("""INSERT INTO repositories
                      (repo_id, full_name, owner_login, description, language, stars, forks, open_issues, created_at, updated_at, html_url, fetched_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                      ON CONFLICT(repo_id) DO UPDATE SET
                        full_name=excluded.full_name, owner_login=excluded.owner_login,
                        description=excluded.description, language=excluded.language,
                        stars=excluded.stars, forks=excluded.forks, open_issues=excluded.open_issues,
                        created_at=excluded.created_at, updated_at=excluded.updated_at,
                        html_url=excluded.html_url, fetched_at=excluded.fetched_at""", values)
                    total += 1
                conn.commit()
                print(f"Page {page}: received {len(items)} repositories")
                if len(items) < PER_PAGE or page * PER_PAGE >= payload.get("total_count", 0):
                    break
                time.sleep(1)  # Small pause between pages.
        print(f"Done. Processed {total} records; database: {DB_PATH}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

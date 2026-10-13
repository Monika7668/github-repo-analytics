# GitHub Repository Analytics Pipeline

A beginner-friendly Data Engineering take-home project: fetch public repository data from the GitHub REST API, preserve raw responses, upsert cleaned records into SQLite, analyse the data with SQL, and display a small Streamlit dashboard.

## 1. Why this API and metric?

GitHub provides useful public metadata such as repository name, programming language, stars, forks, issue counts, and timestamps. These fields allow simple, explainable comparisons. Stars are a rough indicator of community interest, not a measure of software quality. The language distribution reflects only the selected repository sample, not all GitHub projects.

## 2. Architecture

`GitHub REST API -> Python requests -> raw_api_responses + repositories (SQLite) -> SQL aggregations -> Streamlit dashboard`

- **Raw layer:** `raw_api_responses` stores the original JSON payload for each fetched page and the fetch timestamp.
- **Clean layer:** `repositories` stores one current row per GitHub repository ID. The primary key and `ON CONFLICT ... DO UPDATE` make reruns safe and refresh current metrics rather than creating duplicates.
- **Reporting layer:** `sql/analysis.sql` contains reporting queries. Aggregations are computed when queried; a separate reporting table is not necessary for this small project.

## 3. Requirements

- Python 3.10+
- Internet access to `api.github.com`
- No API key required for a basic public-data demo. GitHub rate limits apply. An optional personal access token can be provided as `GITHUB_TOKEN` to increase the available quota; do not commit the token.

## 4. Setup and run

### Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python fetch_data.py
streamlit run dashboard.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python fetch_data.py
streamlit run dashboard.py
```

The dashboard opens in a browser. The fetch script defaults to the top repositories matching `stars:>1000`, sorted by stars, and fetches up to 3 pages of 100 results. Adjust `MAX_PAGES` if needed. The GitHub Search API has its own result and rate limits, so keep the sample modest.

To use an optional token:
- PowerShell: `$env:GITHUB_TOKEN="your_token_here"`
- macOS/Linux: `export GITHUB_TOKEN="your_token_here"`

Never share or commit the token.

## 5. SQL analysis

The included `sql/analysis.sql` covers:
1. Total repository count, stars, and open issues.
2. Top repositories by stars.
3. Repository count and total/average stars by language.
4. Repository creation counts by year.
5. Basic data-quality checks.

Run the queries in a SQLite client or copy individual queries into DB Browser for SQLite. If the `sqlite3` command-line program is installed, run `sqlite3 github_analytics.db < sql/analysis.sql`.

## 6. Reliability and data-quality decisions

- **Pagination:** loops through pages and stops when a page is short or the reported result count is reached.
- **Transient errors:** retries failed requests up to three times with a short exponential delay.
- **Rate limits:** checks GitHub's rate-limit response and waits briefly when the remaining quota is zero. If a limit persists, rerun later or configure a token.
- **Missing values:** missing language becomes `Unknown`; missing or invalid numeric metrics become zero; records without an ID or full name are skipped.
- **Duplicates / reruns:** repository ID is the primary key and records are upserted.
- **Raw traceability:** original page JSON is retained with endpoint, page number, and fetch timestamp.
- **Scope limitation:** this is a demo, not a production ingestion service. It does not include a scheduler, alerting, secrets manager, or comprehensive automated tests.

## 7. Assumptions and trade-offs

- This is a point-in-time sample of highly starred repositories, not a complete GitHub dataset.
- Stars indicate interest only approximately and may change between runs.
- SQLite keeps setup simple and local. PostgreSQL or a cloud warehouse would be more suitable for multi-user or larger workloads.
- SQL is used for reporting logic; Python is used for API interaction, basic validation, and orchestration.
- The assignment asks for a scheduled **or on-demand** pipeline, so this project uses on-demand execution to stay within the 3–4 hour time box.

## 8. AI assistance note (edit to reflect your actual use)

AI assistance was used to brainstorm a simple architecture, review code structure, and improve documentation. I checked the table design and query logic, kept the implementation to Python and basic SQL, and chose SQLite/Streamlit to make the project easy to run and explain. Before submission, I ran the pipeline, checked the database rows, executed the SQL queries, and verified that the dashboard loads. I would only claim checks I personally completed.



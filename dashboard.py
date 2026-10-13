"""Small Streamlit dashboard for the SQLite repository table."""
import os, sqlite3
import pandas as pd
import streamlit as st

DB_PATH = os.getenv("DB_PATH", "github_analytics.db")
st.set_page_config(page_title="GitHub Repository Analytics", layout="wide")
st.title("GitHub Repository Analytics")
st.caption("A small API-to-SQL pipeline demo. Refresh the data by running fetch_data.py.")

@st.cache_data(ttl=60)
def load_data(db_path):
    if not os.path.exists(db_path):
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM repositories", conn)

df = load_data(DB_PATH)
if df.empty:
    st.warning("No data found yet. Run `python fetch_data.py` first, then refresh this page.")
    st.stop()

df["language"] = df["language"].fillna("Unknown").replace("", "Unknown")
for col in ["stars", "forks", "open_issues"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

c1, c2, c3 = st.columns(3)
c1.metric("Repositories", f"{len(df):,}")
c2.metric("Total stars", f"{int(df['stars'].sum()):,}")
c3.metric("Open issues", f"{int(df['open_issues'].sum()):,}")

st.subheader("Top repositories by stars")
top = df.nlargest(10, "stars")[["full_name", "language", "stars", "forks", "open_issues", "html_url"]]
st.dataframe(top, use_container_width=True, hide_index=True,
             column_config={"html_url": st.column_config.LinkColumn("Repository URL")})

left, right = st.columns(2)
with left:
    st.subheader("Repositories by language")
    lang = df.groupby("language", as_index=False).size().sort_values("size", ascending=False).head(10)
    lang = lang.rename(columns={"size": "repository_count"}).set_index("language")
    st.bar_chart(lang)
with right:
    st.subheader("Average stars by language")
    avg = df.groupby("language", as_index=False)["stars"].mean().sort_values("stars", ascending=False).head(10)
    st.bar_chart(avg.set_index("language"))

st.subheader("Explore repositories")
options = sorted(df["language"].unique().tolist())
selected = st.multiselect("Filter by programming language", options, default=options[:min(5, len(options))])
filtered = df[df["language"].isin(selected)] if selected else df
st.dataframe(filtered[["full_name", "language", "stars", "forks", "open_issues", "created_at", "updated_at", "html_url"]]
             .sort_values("stars", ascending=False), use_container_width=True, hide_index=True,
             column_config={"html_url": st.column_config.LinkColumn("Repository URL")})

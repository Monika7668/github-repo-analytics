-- Run with: sqlite3 github_analytics.db < sql/analysis.sql
.headers on
.mode column

-- 1. KPI: total repositories, stars and open issues
SELECT COUNT(*) AS repository_count,
       SUM(stars) AS total_stars,
       SUM(open_issues) AS total_open_issues
FROM repositories;

-- 2. Top 10 repositories by stars
SELECT full_name, language, stars, forks, open_issues, html_url
FROM repositories
ORDER BY stars DESC
LIMIT 10;

-- 3. Programming-language distribution (top 10)
SELECT language, COUNT(*) AS repository_count,
       SUM(stars) AS total_stars,
       ROUND(AVG(stars), 0) AS average_stars
FROM repositories
GROUP BY language
ORDER BY repository_count DESC
LIMIT 10;

-- 4. Repositories created per year
SELECT substr(created_at, 1, 4) AS created_year,
       COUNT(*) AS repository_count
FROM repositories
WHERE created_at IS NOT NULL
GROUP BY substr(created_at, 1, 4)
ORDER BY created_year;

-- 5. Simple data-quality check: missing key values / negative metrics
SELECT
  SUM(CASE WHEN full_name IS NULL OR trim(full_name) = '' THEN 1 ELSE 0 END) AS missing_names,
  SUM(CASE WHEN stars < 0 THEN 1 ELSE 0 END) AS negative_star_counts,
  SUM(CASE WHEN language = 'Unknown' THEN 1 ELSE 0 END) AS unknown_languages
FROM repositories;

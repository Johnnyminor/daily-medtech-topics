# Daily MedTech Topics from FDA RSS

This repository uses **GitHub Actions**, **FDA RSS feeds**, and the **OpenAI API** to generate daily medical device content ideas.

Each day, the workflow:
1. Pulls items from selected FDA RSS feeds
2. Filters for relevant medical device topics
3. Summarizes the most relevant items using OpenAI
4. Evaluates their content potential
5. Creates a GitHub issue with the daily topic report

## What this is for

This project is useful for:
- medical device marketing teams
- content strategists
- clinical communications teams
- regulatory-aware demand generation
- daily content ideation based on FDA activity

## Included FDA feeds

The script currently checks these FDA RSS feeds:

- MedWatch
- Press Releases
- Recalls

These are defined in:

`scripts/generate_medtech_topics.py`

## Repository structure

```text
.github/
  workflows/
    daily-medtech-topics.yml
scripts/
  generate_medtech_topics.py
README.md

# Progress log

Update this as you go. This file *is* the thing you show at BBD — it turns "I've
been learning data engineering" into "here's exactly what I built, what it taught
me, and what I'd do next." Keep entries short and honest.

## How to use it
- After each milestone, add a dated entry: what you built, one thing that surprised
  you, one thing you'd do differently.
- Screenshot `make test` going from red to green over time — visible progress beats
  claims.

---

## Milestone tracker
| Iteration | Status | Date done | Test file            |
|-----------|--------|-----------|----------------------|
| 0 Sample data   | 🔴 | — | (manual)            |
| 1 Warehouse     | 🔴 | — | test_warehouse.py   |
| 2 Ingest        | 🔴 | — | test_ingest.py      |
| 3 Validation    | 🔴 | — | test_validate.py    |
| 4 Governance    | 🔴 | — | test_govern.py      |
| 5 Transform     | 🔴 | — | test_transform.py   |
| 6 Orchestration | 🔴 | — | test_pipeline.py    |

---

## Log

### YYYY-MM-DD — Scaffold set up
- Cloned the skeleton, read the roadmap, got `make setup` working.
- Surprise: _[fill in]_
- Next: Iteration 0 — write the sample-data generator.

<!-- Add new entries above this line, newest first. -->

---

## Talking points for BBD (keep this current)
Rewrite these in your own words as you actually build each part — a point you can
explain from your own code is worth ten you memorised.

1. **Why bronze/silver/gold?** _[your answer]_
2. **How does your pipeline stay idempotent?** _[your answer]_
3. **What happens to a bad row?** _[your answer]_
4. **The passport angle — what does your cross-border report show, and why does it
   matter under POPIA?** _[your answer]_
5. **Point at one local component and name its AWS equivalent.** _[your answer]_

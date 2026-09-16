# passport-pipeline

> *"Your database has a passport."* — Precious Mamotingoe Lesupi, BBD Escape
>
> A local-first batch data pipeline that treats data residency, PII, and trust
> as **engineering constraints baked into the design** — not paperwork bolted on
> at the end.

This is a portfolio project I'm building to go deep on data-engineering
fundamentals before moving to cloud-specific certs and roles. It's deliberately
**local-first and free to run** (no paid AWS account needed), but structured so
that every stage maps cleanly onto managed cloud services later.

---

## The idea

Synthetic South African customer + transaction data flows through a classic
three-layer ("medallion") pipeline. A governance layer runs alongside every
stage, because in the real world the moment data crosses a region boundary,
**POPIA** and cross-border transfer rules become design constraints.

```
                ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  source  ───▶  │   BRONZE    │─▶ │   SILVER    │─▶ │    GOLD     │ ──▶ analytics
  (CSV)         │  raw, as-is │   │ clean,typed,│   │ business-   │
                │             │   │ PII-handled │   │ ready marts │
                └─────────────┘   └─────────────┘   └─────────────┘
                        │                │                 │
                        └────────── governance layer ──────┘
                      (PII detection · masking · residency
                       tagging · data contracts · audit log)
```

The showpiece output is a **cross-border transfer report** — a mart that shows
exactly which personal data was processed outside its home region. That's the
"passport" made visible.

## Local stack (all free)

| Concern            | Tool                    | Maps to (cloud)              |
|--------------------|-------------------------|------------------------------|
| Warehouse          | DuckDB                  | Redshift / BigQuery          |
| Transforms         | Python + SQL            | Glue / dbt                   |
| Data quality       | hand-rolled validators  | Great Expectations / dbt tests |
| Orchestration      | plain Python pipeline   | Airflow / Step Functions     |
| Storage layers     | local `data/` folders   | S3 buckets (bronze/silver/gold) |

Hand-rolling the primitives first is the whole point — it's the "fundamentals
before the fancy tools" advice made concrete. dbt and an orchestrator come in as
stretch milestones once the primitives work.

## Status

This repo ships as a **scaffold**: structure, contracts, docstrings, and a full
test suite that currently **fails on purpose**. My job is to turn the suite green,
one module at a time. See [`ROADMAP.md`](ROADMAP.md) for the build order and
[`PROGRESS.md`](PROGRESS.md) for where I actually am.

```bash
make setup     # create venv + install deps
make test      # run the suite — everything red at the start
make run       # run the pipeline end-to-end (fails at first unbuilt stage)
```

## Repo layout

```
governance/           data contracts (YAML) + the residency policy
src/passport_pipeline/ the pipeline modules I implement (stubs for now)
sql/                   staging + mart SQL models I write
scripts/               sample-data generator I write
tests/                 the executable spec — make these pass
data/                  bronze/silver/gold landing zones (git-ignored)
```

## How I'll present this at BBD

The point isn't a finished product — it's showing I can **reason about the job**.
Talking points I'm building toward (see `PROGRESS.md` for the live version):

1. *Why medallion layers?* — separation of raw/clean/business, and why you never
   mutate raw.
2. *Idempotency* — the pipeline can re-run without duplicating or corrupting data.
3. *Data quality as a gate* — bad rows get quarantined, not silently dropped.
4. *The passport angle* — residency tagging + the cross-border report, tied
   directly to Precious's talk.
5. *Cloud mapping* — I can point at each local component and name its AWS analogue.

That last one is what makes a student sound like they've thought about the real
role, not just followed a tutorial.

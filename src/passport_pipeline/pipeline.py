"""End-to-end orchestration.  [Iteration 6]

The wiring below shows the intended shape and order. Each call routes into a
module you implement, so running this fails at the first unbuilt stage — that's
your to-do list made executable. Fill in the gaps, add logging, and make the whole
thing IDEMPOTENT (running it twice leaves the warehouse in the same state).
"""
from __future__ import annotations

import logging

from . import config, ingest, transform, warehouse

logging.basicConfig(level=config.LOG_LEVEL)
log = logging.getLogger("pipeline")


def run() -> None:
    """Run the full pipeline: ingest -> validate -> govern -> transform."""
    log.info("Connecting to warehouse at %s", config.WAREHOUSE_PATH)
    con = warehouse.connect()
    warehouse.create_schemas(con)

    log.info("Ingesting raw -> bronze")
    counts = ingest.ingest_all(con)
    log.info("Bronze row counts: %s", counts)

    # Validation (Iter 3) and governance (Iter 4) run inside build_silver:
    # it judges bronze against the contracts, quarantines bad rows, masks PII,
    # classifies residency, and writes the audit entry.
    log.info("Transforming bronze -> silver -> gold")
    transform.build_silver(con)
    transform.build_gold(con)

    log.info("Done. Marts are ready in the gold schema.")
    con.close()


if __name__ == "__main__":
    run()

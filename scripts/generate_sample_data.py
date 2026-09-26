"""Generate synthetic SA customer + transaction data.  [Iteration 0]

Run: `make seed`  (i.e. python scripts/generate_sample_data.py)

Writes two CSVs into data/raw/:
  customers.csv     columns per governance/data_contracts/customers.yml
  transactions.csv  columns per governance/data_contracts/transactions.yml

SA ID number structure (13 digits), which is why we build them by hand:
    YYMMDD  birth date
    SSSS    sequence within that day; first digit encodes gender (0-4 F, 5-9 M)
    C       citizenship: 0 = SA citizen, 1 = permanent resident
    A       historically a race digit, now always 8
    Z       Luhn check digit over the first 12

BAD ROWS INJECTED (Iteration 3's validator should catch exactly these):
    customers.csv     4  -> bad_id_checksum, malformed_email, bad_province, null_name
    transactions.csv  5  -> negative_amount, duplicate_txn_id, orphan_customer_id,
                            bad_currency, null_merchant
    total             9

Separately, CROSS_BORDER_COUNT transactions are given a non-af-south-1
processing_region. Those are *valid* rows — they're the ones Iteration 4's
governance layer must flag as cross-border transfers, not reject.
"""
import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

# Standalone on purpose: the package isn't pip-installed, so we don't import
# passport_pipeline.config here. This must stay in step with config.RAW_DIR.
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

SEED = 42
# Dates are anchored to a fixed day rather than "today", so a re-run produces
# byte-identical CSVs. Reproducible input is what lets Iteration 6 prove the
# pipeline is idempotent.
REFERENCE_DATE = date(2026, 9, 27)
REFERENCE_MOMENT = datetime(2026, 9, 27, 23, 59, 59)
N_CUSTOMERS = 200
N_TRANSACTIONS = 1000
CROSS_BORDER_COUNT = 40

# faker has no en_ZA locale, so we mix isiZulu and en_GB name pools — faker
# picks one at random per call, which gives a plausible SA spread of names.
fake = Faker(["zu_ZA", "en_GB"])
Faker.seed(SEED)  # Seed the RNG for reproducibility
rng = random.Random(SEED)  # our own choices, kept separate from faker's

PROVINCES = [
    "Eastern Cape",
    "Free State",
    "Gauteng",
    "KwaZulu-Natal",
    "Limpopo",
    "Mpumalanga",
    "North West",
    "Northern Cape",
    "Western Cape",
]

HOME_REGION = "af-south-1"
FOREIGN_REGIONS = ["eu-west-1", "us-east-1"]

MERCHANTS = [
    "Checkers Sixty60",
    "Takealot",
    "Woolworths",
    "Pick n Pay",
    "Shoprite",
    "Clicks",
    "Dis-Chem",
    "Engen",
    "Uber Eats",
    "Vodacom",
]

CUSTOMER_FIELDS = [
    "customer_id",
    "first_name",
    "last_name",
    "sa_id_number",
    "email",
    "phone",
    "province",
    "signup_date",
    "home_region",
]

TRANSACTION_FIELDS = [
    "transaction_id",
    "customer_id",
    "amount_zar",
    "currency",
    "merchant",
    "txn_timestamp",
    "processing_region",
]

# Each corruption takes a good row and returns a broken copy. Keeping them as
# data (rather than inline edits) means the count of bad rows is obvious.
CUSTOMER_CORRUPTIONS = {
    "bad_id_checksum": lambda r: {**r, "sa_id_number": _break_checksum(r["sa_id_number"])},
    "malformed_email": lambda r: {**r, "email": "thandi.dot.example.com"},
    "bad_province": lambda r: {**r, "province": "Atlantis"},
    "null_name": lambda r: {**r, "first_name": ""},
}

TRANSACTION_CORRUPTIONS = {
    "negative_amount": lambda r: {**r, "amount_zar": "-149.99"},
    "bad_currency": lambda r: {**r, "currency": "USD"},
    "null_merchant": lambda r: {**r, "merchant": ""},
    # duplicate_txn_id and orphan_customer_id need context, so they're applied
    # in corrupt_transactions() rather than here.
}


def luhn_check_digit(digits: str) -> int:
    """Return the Luhn check digit for `digits` (the first 12 of an SA ID).

    Walking right-to-left over the payload, double every second digit and
    subtract 9 if that doubling pushes it past 9. The check digit is whatever
    makes the running total a multiple of 10.
    """
    total = 0
    for position, char in enumerate(reversed(digits)):
        value = int(char)
        if position % 2 == 0:  # every second digit counting from the right
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return (10 - total % 10) % 10


def generate_sa_id(birth_date: date, is_male: bool, citizen: bool = True) -> str:
    """Build a structurally valid 13-digit SA ID number."""
    gender_digit = rng.randint(5, 9) if is_male else rng.randint(0, 4)
    sequence = f"{gender_digit}{rng.randint(0, 999):03d}"
    payload = (
        f"{birth_date:%y%m%d}"
        f"{sequence}"
        f"{0 if citizen else 1}"
        f"8"  # the legacy race digit, always 8 on modern IDs
    )
    return f"{payload}{luhn_check_digit(payload)}"


def _break_checksum(sa_id: str) -> str:
    """Flip the check digit so the ID looks right but fails Luhn."""
    wrong = (int(sa_id[-1]) + 1) % 10
    return f"{sa_id[:-1]}{wrong}"


def random_birth_date() -> date:
    """A birth date for an adult aged 18-80, relative to REFERENCE_DATE.

    We don't use faker's date_of_birth because it is relative to the real
    'today', which would make the output change from one day to the next.
    """
    return REFERENCE_DATE - timedelta(days=rng.randint(18 * 365, 80 * 365))


def sa_phone() -> str:
    """An SA mobile number in +27 format, as the contract expects."""
    prefix = rng.choice(["60", "61", "62", "71", "72", "73", "76", "78", "82", "83", "84"])
    return f"+27{prefix}{rng.randint(0, 9_999_999):07d}"


def make_customer(index: int) -> dict:
    is_male = rng.random() < 0.5
    first_name = fake.first_name_male() if is_male else fake.first_name_female()
    last_name = fake.last_name()
    birth_date = random_birth_date()
    return {
        "customer_id": f"C{index:05d}",
        "first_name": first_name,
        "last_name": last_name,
        "sa_id_number": generate_sa_id(birth_date, is_male),
        "email": f"{first_name}.{last_name}{index}@example.co.za".lower().replace(" ", ""),
        "phone": sa_phone(),
        "province": rng.choice(PROVINCES),
        "signup_date": (
            REFERENCE_DATE - timedelta(days=rng.randint(0, 3 * 365))
        ).isoformat(),
        "home_region": HOME_REGION,
    }


def make_transaction(index: int, customer_ids: list[str], cross_border: bool) -> dict:
    timestamp = REFERENCE_MOMENT - timedelta(
        days=rng.randint(0, 365), seconds=rng.randint(0, 86_399)
    )
    return {
        "transaction_id": f"T{index:06d}",
        "customer_id": rng.choice(customer_ids),
        "amount_zar": f"{rng.uniform(15, 8_500):.2f}",
        "currency": "ZAR",
        "merchant": rng.choice(MERCHANTS),
        "txn_timestamp": timestamp.isoformat(timespec="seconds"),
        "processing_region": rng.choice(FOREIGN_REGIONS) if cross_border else HOME_REGION,
    }


def corrupt(rows: list[dict], corruptions: dict) -> list[dict]:
    """Apply each corruption to a different row, in place, by index."""
    for offset, corrupt_row in enumerate(corruptions.values()):
        rows[offset] = corrupt_row(rows[offset])
    return rows


def corrupt_transactions(rows: list[dict]) -> list[dict]:
    """The three field-level corruptions, plus the two that need context."""
    rows = corrupt(rows, TRANSACTION_CORRUPTIONS)
    # A duplicate primary key — breaks idempotency, so validation must catch it.
    rows[-2] = {**rows[-2], "transaction_id": rows[0]["transaction_id"]}
    # A transaction pointing at a customer who doesn't exist.
    rows[-1] = {**rows[-1], "customer_id": "C99999"}
    return rows


def write_csv(file_path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    """Write a CSV file with the given fieldnames and rows."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    customers = [make_customer(i) for i in range(1, N_CUSTOMERS + 1)]
    customer_ids = [c["customer_id"] for c in customers]

    # Decide up front which transactions cross a border, so the count is exact.
    cross_border_indexes = set(
        rng.sample(range(1, N_TRANSACTIONS + 1), CROSS_BORDER_COUNT)
    )
    transactions = [
        make_transaction(i, customer_ids, cross_border=i in cross_border_indexes)
        for i in range(1, N_TRANSACTIONS + 1)
    ]

    customers = corrupt(customers, CUSTOMER_CORRUPTIONS)
    transactions = corrupt_transactions(transactions)

    write_csv(RAW_DIR / "customers.csv", CUSTOMER_FIELDS, customers)
    write_csv(RAW_DIR / "transactions.csv", TRANSACTION_FIELDS, transactions)

    print(f"Wrote {len(customers)} customers ({len(CUSTOMER_CORRUPTIONS)} bad) "
          f"-> {RAW_DIR / 'customers.csv'}")
    print(f"Wrote {len(transactions)} transactions (5 bad, "
          f"{CROSS_BORDER_COUNT} cross-border) "
          f"-> {RAW_DIR / 'transactions.csv'}")


if __name__ == "__main__":
    main()

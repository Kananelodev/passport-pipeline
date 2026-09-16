"""Generate synthetic SA customer + transaction data.  [Iteration 0]

Run: `make seed`  (i.e. python scripts/generate_sample_data.py)

Write two CSVs into data/raw/:
  customers.csv     columns per governance/data_contracts/customers.yml
  transactions.csv  columns per governance/data_contracts/transactions.yml

Requirements:
  - Use the `faker` library for names/emails/phones (there's a faker 'en_ZA' locale
    — try it). Generate SA ID numbers yourself so you understand their structure.
  - Seed the RNG so runs are reproducible.
  - Deliberately inject a handful of INVALID rows so your validator (Iter 3) has
    something to catch, e.g.:
        * a customer with a bad SA ID checksum,
        * a malformed email,
        * a transaction with a negative amount,
        * a duplicate transaction_id,
        * a transaction whose customer_id doesn't exist,
        * a transaction with processing_region = 'us-east-1' (cross-border).
  - Keep it small (say ~200 customers, ~1000 transactions) so runs are fast.

Leave a comment noting how many bad rows you injected — future-you will want to
check the validator caught exactly that many.
"""


def main() -> None:
    raise NotImplementedError("Iteration 0: build the sample-data generator.")


if __name__ == "__main__":
    main()

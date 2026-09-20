from ingestion import load_raw_data
from validation import initiate_validation

if __name__ == "__main__":
    load_raw_data.main()
    validation_passed = initiate_validation.main()
    if not validation_passed:
        raise RuntimeError(
            "Validation pass rate is below the 70% threshold; transformation stopped."
        )
from ingestion import load_raw_data
from validation import initiate_validation

if __name__ == "__main__":
    load_raw_data.main()
    initiate_validation.main()
import pandas as pd

def load_csv(
    file_path,
    # table_name,
    # schema
):
    df = pd.read_csv(file_path)
    print("Shape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())



load_csv("dataset\Brazilian E-Commerce Public Dataset by Olist.csv")


# python -m src.ingestion.load_raw_data
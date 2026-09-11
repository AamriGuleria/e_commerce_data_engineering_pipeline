import pandas as pd

def load_csv(
    file_path,
    # table_name,
    # schema
):
    df = pd.read_csv(file_path)
    print(df.shape)
    print(df.head())
    print(df.dtypes)



load_csv("dataset\Brazilian E-Commerce Public Dataset by Olist.csv")


# python -m src.ingestion.load_raw_data
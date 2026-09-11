import pandas as pd

df = pd.read_csv("C:\Users\asus\e_commerce_data_engineering_pipeline\dataset\Brazilian E-Commerce Public Dataset by Olist.csv.csv")

print(df.shape)
print(df.head())
print(df.dtypes)


def check_not_null(df,columns):
    return {column : int(df[column].isna().sum()) for column in columns}

def check_duplicates(df,columns):
    return int(df.duplicated(subset=columns).sum())

def check_non_negative(df,columns):
    return {
        column: int((df[column].dropna()<0).sum())
        for column in columns
    }
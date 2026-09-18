
from collections.abc import Iterable


def _ensure_columns(df, columns: Iterable[str]) -> None:
    missing_columns = [column for column in columns if column not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing columns: {missing_columns}")


def check_not_null(df, columns: Iterable[str]) -> dict[str, int]:
    _ensure_columns(df, columns)
    return {column: int(df[column].isna().sum()) for column in columns}


def check_duplicates(df, columns: Iterable[str]) -> int:
    _ensure_columns(df, columns)
    return int(df.duplicated(subset=list(columns)).sum())


def check_non_negative(df, columns: Iterable[str]) -> dict[str, int]:
    _ensure_columns(df, columns)
    return {
        column: int((df[column].dropna() < 0).sum())
        for column in columns
    }


def check_minimum_value(df, minimums: dict[str, int | float]) -> dict[str, int]:
    _ensure_columns(df, minimums)
    return {
        column: int((df[column].dropna() < minimum).sum())
        for column, minimum in minimums.items()
    }
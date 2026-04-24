import pandas as pd

def load_ffiec_data(path_1, path_2):
    df1 = pd.read_csv(path_1, sep="\t", low_memory=False)
    df2 = pd.read_csv(path_2, sep="\t", low_memory=False)

    # Normalize column names
    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    # Merge
    df = df1.merge(
        df2,
        on=["IDRSSD", "Reporting Period End Date"],
        how="inner"
    )

    return df
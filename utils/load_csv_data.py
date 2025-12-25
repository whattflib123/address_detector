import os
import pandas as pd

def load_previous_data(file_path, columns):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)

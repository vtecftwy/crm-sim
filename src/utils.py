import numpy as np
import pandas as pd

from pathlib import Path
from scipy.stats import beta


ROOT = Path(__file__).parent.parent.resolve()

def account_info_generator(random_state=None):
    """Generate a unique account info."""
    p2acct_info = ROOT / 'data/account-info-clean.tsv'
    df = pd.read_csv(p2acct_info, sep='\t')
    df = df.sample(frac=1, random_state=random_state)  # Shuffle the DataFrame
    df = df.reset_index(drop=True)  # Reset index after shuffling   
    idx = 0
    while True:
        row = df.iloc[idx % len(df)]
        yield row
        idx += 1

def salesrep_name_generator():
    """Generate a unique account name."""
    idx = 1
    while True:
        yield f"SalesRep {idx}"
        idx += 1

def draw_value_beta(val_min, val_max):
    """Draw a random sample between val_min and val_max, from beta ."""
    #  Validation
    val_min, val_max = int(val_min), int(val_max)
    if val_min >= val_max:
        raise ValueError(f"val_min ({val_min:,d}) must be less than val_max ({val_max:,d})")

    # Parameters for the Beta distribution (right-skewed)
    alpha = 2
    beta_param = 5
    val = beta.rvs(alpha, beta_param, size=1)

    # Scale samples
    scaled_val = val_min + val * (val_max - val_min)

    return int(scaled_val)

def dict_index(d, idx):
    return d[list(d.keys())[idx]]

    
if __name__ == "__main__":
    account_name_gen = account_info_generator(1988)
    # print(next(account_name_gen).tolist())
    # print(next(account_name_gen).tolist())

    salesrep_name_gen = salesrep_name_generator()
    # print(next(salesrep_name_gen))

    val = draw_value_beta(10_000, 100_000)
    # print(val)
    # print(type(val))


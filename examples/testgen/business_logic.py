import pandas as pd


def spend_per_signup(spend: pd.Series, signups: pd.Series) -> pd.Series:
    """The cost per signup in relation to spend."""
    return spend / signups


def avg_spend(spend: pd.Series) -> float:
    """Average spend."""
    return spend.mean()

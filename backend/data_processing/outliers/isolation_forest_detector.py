"""Isolation Forest outlier detection for a single series (scikit-learn)."""
from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np


def detector(data, contamination='auto'):
    """Flag Isolation-Forest outliers in 'value' as NaN; contamination 'auto' or float."""
    data = data.copy()
    if contamination != 'auto':
        contamination = float(contamination)
    model = IsolationForest(contamination=contamination, random_state=42)
    predictions = model.fit_predict(data[['value']].to_numpy())
    data.loc[predictions == -1, 'value'] = np.nan
    return pd.DataFrame(data)

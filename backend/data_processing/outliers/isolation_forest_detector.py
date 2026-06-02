from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np


def detector(data, contamination='auto'):
    data = data.copy()
    if contamination != 'auto':
        contamination = float(contamination)
    model = IsolationForest(contamination=contamination, random_state=42)
    predictions = model.fit_predict(data[['value']].to_numpy())
    data.loc[predictions == -1, 'value'] = np.nan
    return pd.DataFrame(data)

from sklearn.neighbors import LocalOutlierFactor
import pandas as pd
import numpy as np


def detector(data, contamination='auto'):
    data = data.copy()
    if contamination != 'auto':
        contamination = float(contamination)
    n_neighbors = min(20, max(1, data.shape[0] - 1))
    model = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    predictions = model.fit_predict(data[['value']].to_numpy())
    data.loc[predictions == -1, 'value'] = np.nan
    return pd.DataFrame(data)

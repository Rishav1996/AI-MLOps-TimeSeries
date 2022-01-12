import pandas as pd
import numpy as np
import scipy.stats as stats


def detector(data, z_score=3):
    data = data.copy()
    data['year'] = data.index.year
    data['zscore'] = np.nan
    for i in data['year'].unique():
        data.loc[data['year'] == i, 'zscore'] = stats.zscore(data.loc[data['year'] == i, 'value'].values)
    data['zscore_thresh'] = data['zscore'].abs() > z_score
    data.loc[data['zscore_thresh'], 'value'] = np.nan
    data.drop(columns=['zscore', 'zscore_thresh', 'year'], inplace=True)
    data = pd.DataFrame(data)
    return data

"""Mean imputer for missing values in a single series."""
from sktime.transformations.series.impute import Imputer
import pandas as pd
import numpy as np


def imputer(data, if_zero=False):
    """Fill NaN 'value' entries with the series mean; if_zero treats 0 as missing."""
    data = data.copy()
    if if_zero:
        data['value'] = data['value'].replace(0, np.nan)
    if data['value'].isna().sum():
        impute = Imputer(method="mean")
        data['value'] = impute.fit_transform(data['value'])
    data = pd.DataFrame(data)
    return data

from adtk.detector import OutlierDetector
from adtk.data import validate_series
from sklearn.neighbors import LocalOutlierFactor
import pandas as pd
import numpy as np


def detector(data, contamination='auto'):
    data = data.copy()
    data.reset_index(drop=True, inplace=True)
    data.index = data['period'].map(pd.to_datetime)
    if contamination == 'auto':
        outlier_detector = OutlierDetector(LocalOutlierFactor(contamination=contamination))
    else:
        contamination = float(contamination)
        outlier_detector = OutlierDetector(LocalOutlierFactor(contamination=contamination))
    value_data = validate_series(data[['value']])
    anomalies = outlier_detector.fit_detect(value_data)
    data.loc[anomalies, 'value'] = np.nan
    data = pd.DataFrame(data)
    return data

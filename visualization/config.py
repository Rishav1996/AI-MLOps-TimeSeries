database_utils = {
    'HOST': 'db',
    'PORT': 3306,
    'USER': 'mlops_user',
    'PASSWORD': 'MLOPS1234',
    'DATABASE': 'mlops_ts_fcst',
    'DRIVER': 'mysql+pymysql'
}

ingestion_stages = {
    'ing_start': 1,
    'ing_processing': 2,
    'ing_end': 3,
    'ing_failed': 4,
    'ing_flag': 15
}

data_processing_stages = {
    'data_proc_start': 5,
    'data_proc_processing': 6,
    'data_proc_end': 7,
    'data_proc_failed': 8,
    'data_proc_flag': 16
}

forecasting_stages = {
    'fcst_start': 9,
    'fcst_processing': 10,
    'fcst_end': 11,
    'fcst_failed': 12,
    'fcst_flag': 17
}

data_processing_parameters = {
    'impute_choice': 18,
    'impute_if_zero': 19,
    'outlier_choice': 20,
    'outlier_cnt': 21,
    'zscore_cutoff': 22
}

forecasting_parameters = {
    'test_size': 23,
    'forecast_horizon': 24,
    'model_choice': 25,
    'model_types': 26,
    'auto_ensemble': 27,
    'stacking': 28,
    'data_split': 29
}

data_processing_pipeline_path = 'data_processing/data_processing_pipeline.py'
forecasting_pipeline_path = 'forecasting/forecasting_pipeline.py'

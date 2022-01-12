export const LOGIN_FLAG = "LOGIN_FLAG";
export const APP_FLAG = "APP_FLAG";
export const SECRET_KEY = "public-key-for-time-series-mlops";

export const BASE_LINK = "http://localhost";
export const PORT = ":8000";
export const URL = BASE_LINK + PORT;
export const LOGIN_URL = URL + "/login";
export const SIGNUP_URL = URL + "/signup";
export const UPLOAD_URL = URL + "/upload-ingestion-data";
export const DATA_PRE_PROCESSING_TRAIN_IDS_URL = URL + "/get-dp-train-ids";
export const DATA_PRE_PROCESSING_PARAM_URL = URL + "/get-default-data-processing-parameters";
export const DATA_PRE_PROCESSING_TRIGGER_URL = URL + "/trigger-data-processing";
export const FORECASTING_TRAIN_IDS_URL = URL + "/get-fcst-train-ids";
export const FORECASTING_PARAM_URL = URL + "/get-default-forecasting-parameters";
export const FORECASTING_TRIGGER_URL = URL + "/trigger-forecasting";
export const METRIC_TRIGGER_URL = URL + "/trigger-metrics-calculation";
export const STATUS_URL = URL + "/status";

export const initGlobalState = {
  flag: LOGIN_FLAG,
  user_id: null,
  user_name: null,
};

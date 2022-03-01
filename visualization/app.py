import plotly.express as px
from db_wrapper import get_list_of_train_data_id, get_data, get_metric_data, get_forecast_data
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Visualization", layout="wide",
                   initial_sidebar_state="expanded", page_icon="image/line-chart.png")
st.header("Visualization of Time Series Data")

if 'user_id' in st.experimental_get_query_params().keys():
    user_id = st.experimental_get_query_params()['user_id'][0]
    st.session_state.user_id = user_id[0]
elif 'user_id' in st.session_state.keys():
    user_id = st.session_state.user_id[0]
else:
    st.error('No user_id provided')
    st.stop()

result = get_list_of_train_data_id(user_id)

col1, col2, _ = st.columns([1, 1, 3])
with col1:
    train_id = st.selectbox("Select Train Data", result['train_id'], index=len(result['train_id'])-1)

data_ing_id = result['data_ing_id'][result['train_id'].index(train_id)]
data_dp_id = result['data_dp_id'][result['train_id'].index(train_id)]

data = get_data(data_ing_id, data_dp_id)
with col2:
    ts_id = st.selectbox("Select Time Series", data['ts_id'].unique())

st.markdown('#### Actual and Corrected history')

fig = px.line(data[data['ts_id'] == ts_id], x='period',
              y=['raw_history', 'processed_history'],
              height=500)
fig.update_xaxes(rangeslider_visible=True)
st.plotly_chart(fig, use_container_width=True)

st.download_button('Download Historical Sales Data',
                   data=data.to_csv(index=False), file_name=f'preprocessed_{train_id}.csv')

metric_data = get_metric_data(train_id)
metric_data['split_no'] = metric_data['split_no'].map(int)
metric_data.sort_values(by=['split_no'], inplace=True)

st.markdown('#### Forecast')

col1, col2, _ = st.columns([1, 1, 3])

with col1:
    models_selected = st.selectbox("Select Models", metric_data['model_name'].unique())
with col2:
    split_window = st.selectbox("Select Split Window", metric_data['split_window'].unique())

forecast_result = get_forecast_data(train_id)
forecast_result = forecast_result[forecast_result['ts_id'] == ts_id]
forecast_result = forecast_result[forecast_result['model_name'] == models_selected]
forecast_result = forecast_result[forecast_result['split_window'] == split_window]

fig = px.line(forecast_result, x='period',
              y='raw_history')
fig.add_scatter(x=forecast_result['period'], y=forecast_result['forecast'], name='Forecast')
fig.update_xaxes(rangeslider_visible=True, type='date')
st.plotly_chart(fig, use_container_width=True)

st.download_button('Download Forecasted Sales Data',
                   data=forecast_result.to_csv(index=False), file_name=f'forecasted_{train_id}_{ts_id}.csv')

st.markdown('#### Performance Metrics')
col1, _ = st.columns([1, 4])
with col1:
    performance_metrics = st.selectbox("Select Performance Metrics",
                                       metric_data[~metric_data['metric_name'].isin(['psi', 'ks'])][
                                           'metric_name'].unique())

performance_metrics_data = metric_data[~metric_data['metric_name'].isin(['psi', 'ks'])].copy()
performance_metrics_data = performance_metrics_data[(performance_metrics_data['ts_id'] == ts_id)
                                                    & (performance_metrics_data[
                                                           'metric_name'] == performance_metrics)]
fig = px.histogram(performance_metrics_data,
                   x="model_name", y="metric_value",
                   color='split_no', barmode='group', text_auto=True,
                   facet_row="split_window", labels={'model_name': 'Models', 'metric_value': 'Metric'},
                   category_orders={"split_window": performance_metrics_data[
                       'split_window'].unique()}, histfunc='avg')
st.plotly_chart(fig, use_container_width=True)


def ks_metric(val):
    if val < 0.05:
        return 'Yes'
    else:
        return 'No'


def psi_metric(val):
    if val < 0.1:
        return 'No'
    elif val < 0.2:
        return 'Slight'
    else:
        return 'Extreme'


st.markdown('#### Data Drift Metrics')
col1, _ = st.columns([1, 4])
with col1:
    data_drift_metrics = st.selectbox("Select Drift Metrics",
                                      metric_data[metric_data['metric_name'].isin(['psi', 'ks'])][
                                          'metric_name'].unique())
data_drift_metrics_data = metric_data[metric_data['metric_name'].isin(['psi', 'ks'])]
data_drift_metrics_data = data_drift_metrics_data[(data_drift_metrics_data['ts_id'] == ts_id)
                                                  & (data_drift_metrics_data['metric_name'] == data_drift_metrics)]
if data_drift_metrics == 'ks':
    data_drift_metrics_data['metric_value'] = data_drift_metrics_data['metric_value'].map(ks_metric)
else:
    data_drift_metrics_data['metric_value'] = data_drift_metrics_data['metric_value'].map(psi_metric)

data_drift_view = pd.pivot_table(data_drift_metrics_data[['split_no', 'split_window', 'metric_value']],
                                 index='split_no', columns='split_window', values='metric_value', aggfunc='first')
data_drift_view.reset_index(inplace=True)
data_drift_view.reset_index(inplace=True, drop=True)
st.table(data_drift_view)
if data_drift_metrics == 'ks':
    st.markdown('Note: In ks metric, the value is ```Yes``` if the KS value is less than 0.05, else ```No```')
else:
    st.markdown('Note: In psi metric, the value is ```No``` if the PSI value is less than 0.1. '
                '```Slight``` if the PSI value is between 0.1 and 0.2. '
                '```Extreme``` if the PSI value is greater than 0.2.')

st.download_button('Performance Metrics',
                   data=metric_data.to_csv(index=False), file_name=f'metrics_{train_id}.csv')

score_data = metric_data[(metric_data['ts_id'] == ts_id) & (~metric_data['metric_name'].isin(['psi', 'ks']))].copy()
score_data = pd.pivot_table(score_data, index=['split_no', 'split_window', 'model_name'],
                            columns='metric_name', values='metric_value')
score_data.reset_index(inplace=True)
score_data['key'] = score_data['split_no'].map(str) + '_' + score_data['split_window']
temp = pd.DataFrame()

list_of_performance_metrics = metric_data[~metric_data['metric_name'].isin(['psi', 'ks'])]['metric_name'].unique()

for k in score_data['key'].unique():
    sub_score_data = score_data[score_data['key'] == k].copy()
    for i in list_of_performance_metrics:
        sub_score_data[i] = sub_score_data[i].abs()
        sub_score_data[i] = sub_score_data[i].rank()
        sub_score_data[i] = sub_score_data[i] / sub_score_data[i].sum()
    sub_score_data['score'] = sub_score_data[list_of_performance_metrics].mean(axis=1)
    sub_score_data.drop(columns=list_of_performance_metrics, inplace=True)
    sub_score_data.drop(columns=['key'], inplace=True)
    temp = temp.append(sub_score_data)

score_data = temp.copy()

st.markdown('#### Overall Performance')
fig = px.histogram(score_data,
                   x="model_name", y="score",
                   color='split_no', barmode='group', text_auto=True,
                   facet_row="split_window", labels={'model_name': 'Models', 'score': 'Overall Score'},
                   category_orders={"split_window": score_data['split_window'].unique()}, histfunc='avg')
st.plotly_chart(fig, use_container_width=True)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown('#### Top 3 Stable Models')
    stable_model = score_data.groupby(['split_window', 'model_name']).std().reset_index().copy()
    stable_model = stable_model.sort_values(by=['score'], ascending=True)
    st.table(stable_model.head(3).reset_index(drop=True)[['split_window', 'model_name']])

with col2:
    st.markdown('#### Top 3 Continuous Improving Models')


    def check_improvement(x):
        values = x.values
        if len(values) > 1:
            calc = [1 if values[k] >= values[k + 1] else -1 for k in range(len(values) - 1)]
            calc = sum(calc)
            if calc > 0:
                return calc
            else:
                return 0
        else:
            return values


    score_data.sort_values(by=['split_window', 'model_name', 'split_no'], ascending=True, inplace=True)
    performing_model = score_data.groupby(['split_window', 'model_name']).agg({'score': check_improvement}).reset_index().copy()
    performing_model = performing_model[performing_model['score'] > 0].copy()
    performing_model = performing_model.sort_values(by=['score'], ascending=False)
    st.table(performing_model.head(3).reset_index(drop=True)[['split_window', 'model_name']])

with col3:
    st.markdown('#### Top 3 Models Lowest Average Score')
    average_models = score_data.groupby(['split_window', 'model_name']).mean().reset_index().copy()
    average_models = average_models.sort_values(by=['score'], ascending=True)
    st.table(average_models.head(3).reset_index(drop=True)[['split_window', 'model_name']])

st.download_button('Scoring Metrics',
                   data=score_data.to_csv(index=False), file_name=f'score_{train_id}.csv')

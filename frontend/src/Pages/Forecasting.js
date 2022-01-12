import { Card, Col, Divider, Row, Space } from "antd";
import React, { Component } from "react";
import { Button, Checkbox, Dropdown, Input, Label } from "semantic-ui-react";
import cookies from "react-cookies";
import { fetchGETData, fetchFormData } from "../API";
import {
  FORECASTING_PARAM_URL,
  FORECASTING_TRAIN_IDS_URL,
  FORECASTING_TRIGGER_URL,
  METRIC_TRIGGER_URL,
} from "../constants";
import toast from "react-hot-toast";

export default class Forecasting extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user_id: cookies.load("user_id"),
      train_type: "create",
      train_id: "",
      list_of_train_ids: [],
      default_parameters: {
        model_choice: "",
        model_types: "",
        auto_ensemble: "",
        ensemble: "",
        data_split: "",
        test_size: "",
        forecast_horizon: "",
      },
      possible_parameters: {
        model_choice: [],
        model_types: [],
        data_split: [],
      },
      loadingMetric: false,
    };
  }

  convertArrayToDropdown = (array) => {
    var key_pair = [];
    array.forEach((value) => {
      key_pair.push({ key: value, text: value, value: value });
    });
    return key_pair;
  };

  convertStringToDropdown = (string) => {
    var values = string.split(",");
    var key_pair = [];
    values.forEach((value) => {
      key_pair.push({ key: value, text: value, value: value });
    });
    return key_pair;
  };

  componentDidMount() {
    fetchGETData(FORECASTING_PARAM_URL, this.fetchData);
    let formData = new FormData();
    formData.append("train_type", this.state.train_type);
    formData.append("user_id", parseInt(this.state.user_id));
    fetchFormData(FORECASTING_TRAIN_IDS_URL, this.fetchTrainIds, formData);
  }

  fetchTrainIds = (response) => {
    response = response[0];
    if (response.status === "SUCCESS") {
      var train_ids = response.train_id;
      if (train_ids.length === 0) {
        train_ids = ["No Data"];
      }
      this.setState({
        train_id: train_ids[0],
        list_of_train_ids: this.convertArrayToDropdown(train_ids),
      });
    }
  };

  fetchData = (response) => {
    response = response[0];
    if (response.status === "SUCCESS") {
      var parameters = response.parameters;
      parameters.forEach((parameter) => {
        if (parameter.parameter_name === "model_choice") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              model_choice: parameter.parameter_value,
            },
            possible_parameters: {
              ...this.state.possible_parameters,
              model_choice: this.convertStringToDropdown(
                parameter.parameter_range_values
              ),
            },
          });
        } else if (parameter.parameter_name === "model_types") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              model_types: parameter.parameter_value,
            },
            possible_parameters: {
              ...this.state.possible_parameters,
              model_types: this.convertStringToDropdown(
                parameter.parameter_range_values
              ),
            },
          });
        } else if (parameter.parameter_name === "data_split") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              data_split: parameter.parameter_value,
            },
            possible_parameters: {
              ...this.state.possible_parameters,
              data_split: this.convertStringToDropdown(
                parameter.parameter_range_values
              ),
            },
          });
        } else if (parameter.parameter_name === "test_size") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              test_size: parameter.parameter_value,
            },
          });
        } else if (parameter.parameter_name === "forecast_horizon") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              forecast_horizon: parameter.parameter_value,
            },
          });
        } else if (parameter.parameter_name === "auto_ensemble") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              auto_ensemble: parameter.parameter_value,
            },
          });
        } else if (parameter.parameter_name === "ensemble") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              ensemble: parameter.parameter_value,
            },
          });
        }
      });
    }
  };

  onClickForecasting = (e) => {
    e.preventDefault();
    var parameters = {
      test_size: this.state.default_parameters.test_size,
      forecast_horizon: this.state.default_parameters.forecast_horizon,
      model_choice: this.state.default_parameters.model_choice,
      model_types: this.state.default_parameters.model_types,
      auto_ensemble: this.state.default_parameters.auto_ensemble,
      ensemble: this.state.default_parameters.ensemble,
      data_split: this.state.default_parameters.data_split,
    };
    let formData = new FormData();
    formData.append("user_id", parseInt(this.state.user_id));
    formData.append("train_id", parseInt(this.state.train_id));
    formData.append("parameters", JSON.stringify(parameters));
    formData.append("train_type", this.state.train_type);
    fetchFormData(FORECASTING_TRIGGER_URL, this.onResponse, formData);
  };

  onClickMetric = (e) => {
    e.preventDefault();
    this.setState({
      loadingMetric: true,
    });
    let formData = new FormData();
    formData.append("user_id", parseInt(this.state.user_id));
    formData.append("train_id", parseInt(this.state.train_id));
    fetchFormData(METRIC_TRIGGER_URL, this.onResponse, formData);
  };

  onResponse = (response) => {
    response = response[0];
    if (response.status === "SUCCESS") {
      toast.success(response.message, { position: "bottom-center" });
    } else {
      toast.error(response.message, { position: "bottom-center" });
    }
    this.setState({
      loadingMetric: false,
    });
  };

  render() {
    return (
      <>
        <Card
          style={{
            backgroundColor: "transparent",
            border: "none",
            color: "white",
          }}
        >
          <Row>
            <Col span={14}>
              <Divider style={{ border: "white" }} orientation="center">
                <span style={{ color: "white" }}>Forecasting Parameters</span>
              </Divider>
              <Space direction="vertical" size="large">
                <Space size={20}>
                  <Space size={20} direction="vertical">
                    <span style={{ color: "white" }}>Choose type of Train</span>
                    <Dropdown
                      selection
                      value={this.state.train_type}
                      defaultValue={this.state.train_type}
                      onChange={(e, data) => {
                        let formData = new FormData();
                        formData.append("train_type", data.value);
                        formData.append(
                          "user_id",
                          parseInt(this.state.user_id)
                        );
                        fetchFormData(
                          FORECASTING_TRAIN_IDS_URL,
                          this.fetchTrainIds,
                          formData
                        );
                        this.setState({ train_type: data.value });
                      }}
                      name="train_type"
                      options={[
                        {
                          key: "create",
                          text: "create",
                          value: "create",
                        },
                        {
                          key: "existing",
                          text: "existing",
                          value: "existing",
                        },
                      ]}
                    ></Dropdown>
                  </Space>
                  <Space size={20} direction="vertical">
                    <span style={{ color: "white" }}>Select Train ID</span>
                    <Dropdown
                      selection
                      name="train_id"
                      defaultValue={this.state.train_id}
                      value={this.state.train_id}
                      onChange={(e, data) => {
                        this.setState({ train_id: data.value });
                      }}
                      options={this.state.list_of_train_ids}
                    ></Dropdown>
                  </Space>
                </Space>
                <Space size={20}>
                  <Space size={20} direction="vertical">
                    <span style={{ color: "white" }}>Type of Training</span>
                    <Dropdown
                      selection
                      name="model_choice"
                      defaultValue={this.state.default_parameters.model_choice}
                      value={this.state.default_parameters.model_choice}
                      onChange={(e, data) => {
                        this.setState({
                          default_parameters: {
                            ...this.state.default_parameters,
                            model_choice: data.value,
                          },
                        });
                      }}
                      options={this.state.possible_parameters.model_choice}
                    ></Dropdown>
                  </Space>
                  <Space size={20} direction="vertical">
                    <span style={{ color: "white" }}>Choose Model Type</span>
                    <Dropdown
                      selection
                      name="model_type"
                      multiple={
                        this.state.default_parameters.model_choice === "single"
                          ? false
                          : true
                      }
                      defaultValue={
                        this.state.default_parameters.model_choice === "single"
                          ? this.state.default_parameters.model_types
                          : this.state.default_parameters.model_types.split(",")
                      }
                      value={this.state.default_parameters.model_types}
                      onChange={(e, data) => {
                        if (
                          this.state.default_parameters.model_choice ===
                          "single"
                        ) {
                          this.setState({
                            default_parameters: {
                              ...this.state.default_parameters,
                              model_types: data.value,
                            },
                          });
                        } else {
                          this.setState({
                            default_parameters: {
                              ...this.state.default_parameters,
                              model_types:
                                this.state.default_parameters.model_types +
                                "," +
                                data.value.join(","),
                            },
                          });
                        }
                      }}
                      options={this.state.possible_parameters.model_types}
                    ></Dropdown>
                  </Space>
                  <Space size={20} direction="vertical">
                    <span style={{ color: "white" }}>Type of Data Split</span>
                    <Dropdown
                      selection
                      name="data_split"
                      defaultValue={this.state.default_parameters.data_split}
                      value={this.state.default_parameters.data_split}
                      onChange={(e, data) => {
                        this.setState({
                          default_parameters: {
                            ...this.state.default_parameters,
                            data_split: data.value,
                          },
                        });
                      }}
                      options={this.state.possible_parameters.data_split}
                    ></Dropdown>
                  </Space>
                </Space>
                <Space size={20}>
                  <Space size={20} direction="vertical">
                    <span style={{ color: "white" }}>Test Size</span>
                    <Input
                      name="test_size"
                      defaultValue={this.state.default_parameters.test_size}
                      value={this.state.default_parameters.test_size}
                      onChange={(e, data) => {
                        this.setState({
                          default_parameters: {
                            ...this.state.default_parameters,
                            test_size: data.value,
                          },
                        });
                      }}
                    ></Input>
                  </Space>
                  <Space size={20} direction="vertical">
                    <span style={{ color: "white" }}>Forecast Horizon</span>
                    <Input
                      name="test_size"
                      defaultValue={
                        this.state.default_parameters.forecast_horizon
                      }
                      value={this.state.default_parameters.forecast_horizon}
                      onChange={(e, data) => {
                        this.setState({
                          default_parameters: {
                            ...this.state.default_parameters,
                            forecast_horizon: data.value,
                          },
                        });
                      }}
                    ></Input>
                  </Space>
                </Space>
                <Space size={20}>
                  <Space size={20} direction="vertical">
                    <Checkbox
                      name="auto_ensemble"
                      label={{
                        children: (
                          <span style={{ color: "white" }}>Auto Ensemble</span>
                        ),
                      }}
                      defaultValue={this.state.default_parameters.auto_ensemble}
                      value={this.state.default_parameters.auto_ensemble}
                      onChange={(e, data) => {
                        this.setState({
                          default_parameters: {
                            ...this.state.default_parameters,
                            auto_ensemble: (() => {
                              if (
                                this.state.default_parameters.auto_ensemble ===
                                "0"
                              ) {
                                return "1";
                              } else {
                                return "0";
                              }
                            })(),
                          },
                        });
                      }}
                    ></Checkbox>
                  </Space>
                  <Space size={20} direction="vertical">
                    <Checkbox
                      name="ensemble"
                      label={{
                        children: (
                          <span style={{ color: "white" }}>Ensemble</span>
                        ),
                      }}
                      defaultValue={this.state.default_parameters.ensemble}
                      value={this.state.default_parameters.ensemble}
                      onChange={(e, data) => {
                        this.setState({
                          default_parameters: {
                            ...this.state.default_parameters,
                            ensemble: (() => {
                              if (
                                this.state.default_parameters.ensemble === "0"
                              ) {
                                return "1";
                              } else {
                                return "0";
                              }
                            })(),
                          },
                        });
                      }}
                    ></Checkbox>
                  </Space>
                </Space>
                <Space size={20}>
                  <Button
                    onClick={this.onClickForecasting}
                    style={{ marginTop: 10 }}
                    color="blue"
                  >
                    Trigger Forecasting
                  </Button>
                  <Button
                    onClick={this.onClickMetric}
                    style={{ marginTop: 10 }}
                    color="orange"
                    loading={this.state.loadingMetric}
                  >
                    Trigger Metric
                  </Button>
                </Space>
              </Space>
            </Col>
            <Col span={2}></Col>
            <Col span={8}>
              <Divider style={{ border: "white" }} orientation="center">
                <span style={{ color: "white" }}>Sample Parameters</span>
              </Divider>
              <Space direction="vertical" size="small">
                <span style={{ color: "white" }}>
                  <Label color="blue" ribbon>
                    Model Type :
                  </Label>
                  <br />
                  These are the list of models that currently supported by the
                  system.
                  <br />
                  <ol>
                    <li>ARIMA</li>
                    <li>Exponential Smoothing</li>
                    <li>Naive</li>
                    <li>Polynomial Trend</li>
                    <li>Prophet</li>
                    <li>Theta</li>
                  </ol>
                </span>
                <span style={{ color: "white" }}>
                  <Label color="blue" ribbon>
                    Type of Data Split :
                  </Label>
                  Either you can split the data in expanding manner or sliding
                  the window size or both.
                </span>
                <span style={{ color: "white" }}>
                  <Label color="blue" ribbon>
                    Test Size :
                  </Label>
                  By Default the test size is 0.5 i.e is 50% of the data will be
                  used for testing.
                </span>
                <span style={{ color: "white" }}>
                  <Label color="blue" ribbon>
                    Forecast Horizon :
                  </Label>
                  By default the forecast horizon is 0.1 i.e the forecast length
                  will the 10% of the test data.
                </span>
                <span style={{ color: "white" }}>
                  <Label color="blue" ribbon>
                    Auto-Ensemble or Ensemble :
                  </Label>
                  By default the auto-ensemble and ensemble are turned off. This
                  is mostly used for enhancing the model results by aggregating
                  the results or applying a tree based regression.
                </span>
              </Space>
            </Col>
          </Row>
        </Card>
      </>
    );
  }
}

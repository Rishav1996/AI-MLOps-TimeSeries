import { Card, Col, Divider, Row, Space } from "antd";
import React, { Component } from "react";
import { Button, Checkbox, Dropdown, Input, Label } from "semantic-ui-react";
import cookies from "react-cookies";
import { fetchGETData, fetchFormData } from "../API";
import {
  DATA_PRE_PROCESSING_PARAM_URL,
  DATA_PRE_PROCESSING_TRAIN_IDS_URL,
  DATA_PRE_PROCESSING_TRIGGER_URL,
} from "../constants";
import toast from "react-hot-toast";

export default class DataPreProcessing extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user_id: cookies.load("user_id"),
      train_type: "create",
      train_id: "",
      list_of_train_ids: [],
      default_parameters: {
        outlier_cnt: "",
        outlier_choice: "",
        zscore_cutoff: "",
        impute_choice: "",
        impute_if_zero: "",
      },
      possible_parameters: {
        outlier_choice: [],
        impute_choice: [],
        impute_if_zero: [],
      },
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
    fetchGETData(DATA_PRE_PROCESSING_PARAM_URL, this.fetchData);
    let formData = new FormData();
    formData.append("train_type", this.state.train_type);
    formData.append("user_id", parseInt(this.state.user_id));
    fetchFormData(
      DATA_PRE_PROCESSING_TRAIN_IDS_URL,
      this.fetchTrainIds,
      formData
    );
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
        if (parameter.parameter_name === "outlier_choice") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              outlier_choice: parameter.parameter_value,
            },
            possible_parameters: {
              ...this.state.possible_parameters,
              outlier_choice: this.convertStringToDropdown(
                parameter.parameter_range_values
              ),
            },
          });
        } else if (parameter.parameter_name === "impute_choice") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              impute_choice: parameter.parameter_value,
            },
            possible_parameters: {
              ...this.state.possible_parameters,
              impute_choice: this.convertStringToDropdown(
                parameter.parameter_range_values
              ),
            },
          });
        } else if (parameter.parameter_name === "impute_if_zero") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              impute_if_zero: parameter.parameter_value,
            },
            possible_parameters: {
              ...this.state.possible_parameters,
              impute_if_zero: this.convertStringToDropdown(
                parameter.parameter_range_values
              ),
            },
          });
        } else if (parameter.parameter_name === "zscore_cutoff") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              zscore_cutoff: parameter.parameter_value,
            },
          });
        } else if (parameter.parameter_name === "outlier_cnt") {
          this.setState({
            default_parameters: {
              ...this.state.default_parameters,
              outlier_cnt: parameter.parameter_value,
            },
          });
        }
      });
    }
  };

  onClickPreProcessing = (e) => {
    e.preventDefault();
    var parameters = {
      impute_choice: this.state.default_parameters.impute_choice,
      impute_if_zero: this.state.default_parameters.impute_if_zero,
      outlier_choice: this.state.default_parameters.outlier_choice,
      outlier_cnt: this.state.default_parameters.outlier_cnt,
      zscore_cutoff: this.state.default_parameters.zscore_cutoff,
    };
    var formData = new FormData();
    formData.append("user_id", parseInt(this.state.user_id));
    formData.append("train_id", parseInt(this.state.train_id));
    formData.append("parameters", JSON.stringify(parameters));
    formData.append("train_type", this.state.train_type);
    fetchFormData(DATA_PRE_PROCESSING_TRIGGER_URL, this.onResponse, formData);
  };

  onResponse = (response) => {
    response = response[0];
    if (response.status === "SUCCESS") {
      toast.success(response.message, { position: "bottom-center" });
    }
  };

  render() {
    var outlier_cut_off_ui = {};

    if (this.state.default_parameters.outlier_choice !== "zscore") {
      outlier_cut_off_ui = (
        <Space size={20} direction="vertical">
          <span style={{ color: "white" }}>Contamination %</span>
          <Input
            name="outlier_cnt"
            defaultValue={this.state.default_parameters.outlier_cnt}
            value={this.state.default_parameters.outlier_cnt}
            onChange={(e, data) => {
              this.setState({
                default_parameters: {
                  ...this.state.default_parameters,
                  outlier_cnt: data.value,
                },
              });
            }}
          ></Input>
        </Space>
      );
    } else {
      outlier_cut_off_ui = (
        <Space size={20} direction="vertical">
          <span style={{ color: "white" }}>Z-Score Threshold</span>
          <Input
            name="zscore_cutoff"
            defaultValue={this.state.default_parameters.zscore_cutoff}
            value={this.state.default_parameters.zscore_cutoff}
            onChange={(e, data) => {
              this.setState({
                default_parameters: {
                  ...this.state.default_parameters,
                  zscore_cutoff: data.value,
                },
              });
            }}
          ></Input>
        </Space>
      );
    }

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
                <span style={{ color: "white" }}>
                  Data Pre-Processing Parameters
                </span>
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
                          DATA_PRE_PROCESSING_TRAIN_IDS_URL,
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
                    <span style={{ color: "white" }}>
                      Outlier Correction Choice
                    </span>
                    <Dropdown
                      selection
                      name="outlier_choice"
                      onChange={(e, data) => {
                        this.setState({
                          default_parameters: {
                            ...this.state.default_parameters,
                            outlier_choice: data.value,
                          },
                        });
                      }}
                      value={this.state.default_parameters.outlier_choice}
                      defaultValue={
                        this.state.default_parameters.outlier_choice
                      }
                      options={this.state.possible_parameters.outlier_choice}
                    ></Dropdown>
                  </Space>
                  {outlier_cut_off_ui}
                </Space>
                <Space size={20}>
                  <Space size={20} direction="vertical">
                    <span style={{ color: "white" }}>Imputation Choice</span>
                    <Dropdown
                      selection
                      name="impute_choice"
                      onChange={(e, data) => {
                        this.setState({
                          default_parameters: {
                            ...this.state.default_parameters,
                            impute_choice: data.value,
                          },
                        });
                      }}
                      defaultValue={this.state.default_parameters.impute_choice}
                      value={this.state.default_parameters.impute_choice}
                      options={this.state.possible_parameters.impute_choice}
                    ></Dropdown>
                  </Space>
                </Space>
                <Space size={20} direction="vertical">
                  <span style={{ color: "white" }}>Imputation If Zero</span>
                  <Checkbox
                    selection
                    name="impute_if_zero"
                    onChange={(e, data) => {
                      this.setState({
                        default_parameters: {
                          ...this.state.default_parameters,
                          impute_if_zero: (() => {
                            if (
                              this.state.default_parameters.impute_if_zero ===
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
                    defaultValue={this.state.default_parameters.impute_if_zero}
                    value={this.state.default_parameters.impute_if_zero}
                    options={this.state.possible_parameters.impute_if_zero}
                  ></Checkbox>
                </Space>
                <Button
                  onClick={this.onClickPreProcessing}
                  style={{ marginTop: 10 }}
                  color="blue"
                >
                  Trigger Data Pre-Processing
                </Button>
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
                    Outlier Choice Type :
                  </Label>
                  <br />
                  These are the list of outlier techniques currently available
                  <br />
                  <ul>
                    <li>
                      <b>if</b> : Isolation Forest
                    </li>
                    <li>
                      <b>lof</b> : Local Outlier Factor
                    </li>
                    <li>
                      <b>zscore</b> : Z-Score
                    </li>
                  </ul>
                </span>
                <span style={{ color: "white" }}>
                  <Label color="blue" ribbon>
                    Contamination % :
                  </Label>
                  Either you can give <b>"auto"</b> or any percentage value but
                  less than 1.
                </span>
                <br />
                <span style={{ color: "white" }}>
                  <Label color="blue" ribbon>
                    Z-Score Threshold :
                  </Label>
                  By default it is set to 3 but you can change it to any value.
                </span>
                <br />
                <span style={{ color: "white" }}>
                  <Label color="blue" ribbon>
                    Imputation Choice :
                  </Label>
                  <br />
                  These are the list of imputation techniques currently
                  available.
                  <br />
                  <ul>
                    <li>
                      <b>linear</b>
                    </li>
                    <li>
                      <b>mean</b>
                    </li>
                    <li>
                      <b>median</b>
                    </li>
                    <li>
                      <b>mode</b>
                    </li>
                  </ul>
                </span>
                <span style={{ color: "white" }}>
                  <Label color="blue" ribbon>
                    Imputation If Zero :
                  </Label>
                  By default it is false, but this is done to impute the zero
                  values with imputation choice.
                </span>
              </Space>
            </Col>
          </Row>
        </Card>
      </>
    );
  }
}

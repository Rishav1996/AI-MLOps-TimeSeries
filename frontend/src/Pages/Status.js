import { Card, Tag } from "antd";
import React, { Component } from "react";
import cookies from "react-cookies";
import { Table } from "rsuite";
import { fetchFormData } from "../API";
import { STATUS_URL } from "../constants";
import "rsuite/dist/rsuite.min.css";

import {
  CheckCircleOutlined,
  SyncOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from "@ant-design/icons";

const defaultColumns = [
  {
    key: "train_id",
    label: "Train ID",
    width: 70,
  },
  {
    key: "data_ing_id",
    label: "Ingestion ID",
    width: 150,
  },
  {
    key: "data_dp_id",
    label: "Data Pre-Processing ID",
    width: 150,
  },
  {
    key: "data_fcst_id",
    label: "Forecasting ID",
    width: 150,
  },
  {
    key: "ing_time",
    label: "Ingestion Interval",
    flexGrow: 80,
  },
  {
    key: "dp_time",
    label: "Data Pre-Processing Interval",
    flexGrow: 80,
  },
  {
    key: "fcst_time",
    label: "Forecasting Interval",
    flexGrow: 80,
  },
  {
    key: "phase",
    label: "Stage",
    flexGrow: 80,
  },
  {
    key: "c_status",
    label: "Status",
    flexGrow: 80,
  },
];

const CustomCell = ({ rowData, dataKey, ...props }) => {
  if (dataKey === "phase") {
    if (rowData[dataKey] === "ING") {
      return <Table.Cell {...props}>Ingest</Table.Cell>;
    } else if (rowData[dataKey] === "DP") {
      return <Table.Cell {...props}>Data Pre-Process</Table.Cell>;
    } else if (rowData[dataKey] === "FCST") {
      return <Table.Cell {...props}>Forecast</Table.Cell>;
    } else {
      return <Table.Cell {...props}>Unknown</Table.Cell>;
    }
  } else if (dataKey === "c_status") {
    if (rowData[dataKey] === "S") {
      return (
        <Table.Cell {...props}>
          <Tag
            style={{ backgroundColor: "transparent", color: "white" }}
            icon={<ExclamationCircleOutlined />}
            color="default"
          >
            Starting
          </Tag>
        </Table.Cell>
      );
    } else if (rowData[dataKey] === "F") {
      return (
        <Table.Cell {...props}>
          <Tag
            style={{ backgroundColor: "transparent" }}
            icon={<CloseCircleOutlined />}
            color="error"
          >
            Failed
          </Tag>
        </Table.Cell>
      );
    } else if (rowData[dataKey] === "P") {
      return (
        <Table.Cell {...props}>
          <Tag
            style={{ backgroundColor: "transparent" }}
            icon={<SyncOutlined spin />}
            color="processing"
          >
            Processing
          </Tag>
        </Table.Cell>
      );
    } else if (rowData[dataKey] === "E") {
      return (
        <Table.Cell {...props}>
          <Tag
            style={{ backgroundColor: "transparent" }}
            icon={<CheckCircleOutlined />}
            color="success"
          >
            Completed
          </Tag>
        </Table.Cell>
      );
    }
  } else {
    return <Table.Cell {...props}>{rowData[dataKey]}</Table.Cell>;
  }
};

export default class Status extends Component {
  interval_id = null;

  constructor(props) {
    super(props);
    this.state = {
      user_id: cookies.load("user_id"),
      status: [],
    };
  }

  componentDidMount() {
    this.interval_id = setInterval(() => {
      let formData = new FormData();
      formData.append("user_id", parseInt(this.state.user_id));
      fetchFormData(STATUS_URL, this.fetchStatus, formData);
    }, 1000);
  }

  componentWillUnmount() {
    clearInterval(this.interval_id);
  }

  fetchStatus = (response) => {
    response = response[0];
    if (response.status === "SUCCESS") {
      this.setState({
        status: JSON.parse(response.data),
      });
    }
  };

  render() {
    return (
      <>
        <Card
          padded
          style={{
            backgroundColor: "transparent",
            border: "none",
            color: "white",
            overflowY: "scroll",
            height: "90vh",
          }}
        >
          <Table
            height="800"
            bordered={false}
            hover={false}
            data={this.state.status}
          >
            {defaultColumns.map((column) => {
              const { key, label, ...rest } = column;
              return (
                <Table.Column
                  style={{ backgroundColor: "#222222", color: "white" }}
                  {...rest}
                  key={key}
                  align="center"
                  limit={100}
                  loading={this.state.status.length === 0}
                >
                  <Table.HeaderCell>{label}</Table.HeaderCell>
                  <CustomCell dataKey={key} />
                </Table.Column>
              );
            })}
          </Table>
        </Card>
      </>
    );
  }
}

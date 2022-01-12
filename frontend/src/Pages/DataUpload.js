import React, { Component } from "react";
import cookie from "react-cookies";
import { Col, Divider, Row, Card, Upload } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import toast from "react-hot-toast";
import { Button } from "semantic-ui-react";
import { UPLOAD_URL } from "../constants";
import { fetchFormData } from "../API";

const { Dragger } = Upload;

export default class DataUpload extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user_name: cookie.load("user_name"),
      user_id: parseInt(cookie.load("user_id")),
      file: null,
    };
  }

  setFile = (file) => {
    this.setState({
      file: file,
    });
  };

  handleUpload = (e) => {
    e.preventDefault();
    const { file, user_id } = this.state;
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", user_id);
      fetchFormData(UPLOAD_URL, this.uploadResult, formData);
    }
  };

  uploadResult = (response) => {
    response = response[0];
    if (response.status === "SUCCESS") {
      toast.success(
        "Please refer to Train ID : " +
          response.train_id +
          " and Data ID : " +
          response.data_id,
        {
          position: "bottom-center",
        }
      );
    } else {
      toast.error(response.message, { position: "bottom-center" });
    }
  };

  render() {
    console.log(this.state);
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
                <span style={{ color: "white" }}>Upload Data here</span>
              </Divider>
              <div style={{ height: "400px" }}>
                <Dragger
                  name="file"
                  multiple={false}
                  accept="text/csv"
                  style={{
                    backgroundColor: "rgba(255, 255, 255, 0.1)",
                    backdropFilter: "blur(10px)",
                    border: "none",
                    borderRadius: "10px",
                  }}
                  onChange={(info) => {
                    this.setFile(info.file.originFileObj);
                  }}
                >
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined style={{ color: "white" }} />
                  </p>
                  <p className="ant-upload-text" style={{ color: "white" }}>
                    Click or drag file to this area to upload
                  </p>
                  <p className="ant-upload-hint" style={{ color: "white" }}>
                    Upload only single file at a time
                  </p>
                </Dragger>
              </div>
              <br />
              <Button
                style={{
                  display: "block",
                  marginLeft: "auto",
                  marginRight: "auto",
                  width: "150px",
                  minWidth: "100px",
                }}
                color="blue"
                onClick={this.handleUpload}
              >
                Confirm
              </Button>
            </Col>
            <Col span={2}></Col>
            <Col span={8}>
              <Divider style={{ border: "white" }} orientation="center">
                <span style={{ color: "white" }}>Sample Dataset</span>
              </Divider>
              <span>
                This is how the sample data looks, here{" "}
                <i>
                  <b>ts_id</b>
                </i>{" "}
                are the time series ids, in{" "}
                <i>
                  <b>period</b>
                </i>{" "}
                we should be passing dates and in{" "}
                <i>
                  <b>value</b>
                </i>{" "}
                we should be passing our varrying timepoints.{" "}
              </span>
              <br />
              <br />
              <table id="sample-data">
                <tr>
                  <th>ts_id</th>
                  <th>period</th>
                  <th>value</th>
                </tr>
                <tr>
                  <td>1</td>
                  <td>01-01-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>1</td>
                  <td>01-02-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>1</td>
                  <td>01-03-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>1</td>
                  <td>01-04-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>1</td>
                  <td>01-05-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>1</td>
                  <td>01-06-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>2</td>
                  <td>01-01-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>2</td>
                  <td>01-02-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>2</td>
                  <td>01-03-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>2</td>
                  <td>01-04-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>2</td>
                  <td>01-05-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
                <tr>
                  <td>2</td>
                  <td>01-06-2020</td>
                  <td>{parseInt(100 * Math.random())}</td>{" "}
                </tr>
              </table>
            </Col>
          </Row>
        </Card>
      </>
    );
  }
}

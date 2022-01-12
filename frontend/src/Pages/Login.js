import React, { Component } from "react";
import { Card, Col, Input, Row, Space } from "antd";
import { Button, Image } from "semantic-ui-react";
import image from "../images/time-series-logo.png";
import { APP_FLAG, LOGIN_URL, SIGNUP_URL } from "../constants";
import { fetchData } from "../API";
import cookie from "react-cookies";
import toast from "react-hot-toast";

export default class Login extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user_name: "",
      user_password: "",
    };
  }

  onLoginClick = (e) => {
    e.preventDefault();
    fetchData(LOGIN_URL, this.fetchLoginResult, {
      user_name: this.state.user_name,
      user_password: this.state.user_password,
    });
  };

  onSignUp = (e) => {
    e.preventDefault();
    fetchData(SIGNUP_URL, this.fetchSignUpResult, {
      user_name: this.state.user_name,
      user_password: this.state.user_password,
    });
  };

  fetchSignUpResult = (response) => {
    response = response[0];
    if (response.status === "SUCCESS") {
      toast.success(response.message, { position: "bottom-center" });
    } else {
      toast.error(response.message, { position: "bottom-center" });
    }
  };

  fetchLoginResult = (response) => {
    response = response[0];
    if (response.status === "SUCCESS") {
      toast.success("Login Successful !!", { position: "bottom-center" });
      cookie.save("user_id", response.user_id, { path: "/" });
      cookie.save("user_name", this.state.user_name, { path: "/" });
      cookie.save("flag", APP_FLAG, { path: "/" });
      this.props.global_state({
        flag: APP_FLAG,
        user_id: response.user_id,
        user_name: this.state.user_name,
      });
    } else {
      toast.error("Login failed !!", { position: "bottom-center" });
    }
  };

  render() {
    return (
      <>
        <Row>
          <Col className="page-login" md={14}>
            <Space
              size={24}
              style={{ width: "80%" }}
              align="center"
              direction="vertical"
            >
              <Image width="350px" src={image}></Image>
              <h1 style={{ color: "white", float: "right" }}>
                Time Series MLOps
              </h1>
            </Space>
          </Col>
          <Col className="page-login" md={10}>
            <Card className="page-login-card">
              <Space size={24} style={{ width: "80%" }} direction="vertical">
                <Input
                  style={{
                    backgroundColor: "black",
                    color: "white",
                    border: "none",
                    height: "50px",
                  }}
                  onChange={(e) => {
                    this.setState({ user_name: e.target.value });
                  }}
                  placeholder="Username"
                />
                <Input
                  style={{
                    backgroundColor: "black",
                    color: "white",
                    border: "none",
                    height: "50px",
                  }}
                  onChange={(e) => {
                    this.setState({ user_password: e.target.value });
                  }}
                  placeholder="Password"
                  type="password"
                />
                <Space style={{ float: "right" }}>
                  <Button color="green" onClick={this.onLoginClick}>
                    Login
                  </Button>
                  <Button color="blue" onClick={this.onSignUp}>
                    Sign Up
                  </Button>
                </Space>
              </Space>
            </Card>
          </Col>
        </Row>
      </>
    );
  }
}

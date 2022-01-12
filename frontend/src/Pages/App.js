import React, { Component } from "react";
import { Menu } from "semantic-ui-react";
import { LOGIN_FLAG } from "../constants";
import cookie from "react-cookies";
import toast from "react-hot-toast";
import DataUpload from "./DataUpload";
import DataPreProcessing from "./DataPreProcessing";
import Status from "./Status";
import Forecasting from "./Forecasting";
import { UserOutlined } from "@ant-design/icons";
import { Space } from "antd";

const menu_keys = [
  "data_upload",
  "data_pre_processing",
  "forecasting",
  "status",
];

export default class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user_name: props.state.user_name,
      user_id: props.state.user_id,
      active_key: menu_keys[0],
    };
  }

  onChangeActiveMenu = (e, { name }) => {
    this.setState({
      active_key: name,
    });
  };

  onLogoutClick = () => {
    toast.success("Logout Successful !!", { position: "bottom-center" });
    cookie.remove("user_name");
    cookie.remove("user_id");
    cookie.save("flag", LOGIN_FLAG, { path: "/" });
    this.props.global_state({
      flag: LOGIN_FLAG,
      user_id: null,
      user_name: null,
    });
  };

  render() {
    var container_show = null;

    if (this.state.active_key === menu_keys[0]) {
      container_show = <DataUpload />;
    } else if (this.state.active_key === menu_keys[1]) {
      container_show = <DataPreProcessing />;
    } else if (this.state.active_key === menu_keys[2]) {
      container_show = <Forecasting />;
    } else if (this.state.active_key === menu_keys[3]) {
      container_show = <Status />;
    }

    return (
      <>
        <Menu secondary inverted color="blue">
          <Menu.Item>
            <Space align="baseline" size="middle">
              <UserOutlined />
              {this.state.user_name}
            </Space>
          </Menu.Item>
          <Menu.Item
            name={menu_keys[0]}
            onClick={this.onChangeActiveMenu}
            key={menu_keys[0]}
            active={menu_keys[0] === this.state.active_key}
          >
            Data Upload
          </Menu.Item>
          <Menu.Item
            name={menu_keys[1]}
            onClick={this.onChangeActiveMenu}
            key={menu_keys[1]}
            active={menu_keys[1] === this.state.active_key}
          >
            Pre-Processing
          </Menu.Item>
          <Menu.Item
            name={menu_keys[2]}
            onClick={this.onChangeActiveMenu}
            key={menu_keys[2]}
            active={menu_keys[2] === this.state.active_key}
          >
            Forecasting
          </Menu.Item>
          <Menu.Item
            name={menu_keys[3]}
            onClick={this.onChangeActiveMenu}
            active={menu_keys[3] === this.state.active_key}
          >
            Status
          </Menu.Item>
          <Menu.Menu position="right">
            <Menu.Item>
              <a target="_blank" href="localhost:5555">
                Task Monitor
              </a>
            </Menu.Item>
            <Menu.Item>
              <a target="_blank" href={"localhost:8501/?user_id="+this.state.user_id}>
                Visualization
              </a>
            </Menu.Item>
            <Menu.Item onClick={this.onLogoutClick}>
              <span style={{ color: "orange" }}>
                <b>Logout</b>
              </span>
            </Menu.Item>
          </Menu.Menu>
        </Menu>
        <div>{container_show}</div>
      </>
    );
  }
}

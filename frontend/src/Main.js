import React, { Component } from "react";
import { LOGIN_FLAG, APP_FLAG, initGlobalState } from "./constants";
import Login from "./Pages/Login";
import App from "./Pages/App";
import cookie from "react-cookies";

export default class Main extends Component {
  constructor(props) {
    super(props);
    this.state = {
      ...initGlobalState,
    };
  }

  componentDidMount() {
    if (cookie.load("flag") === APP_FLAG) {
      this.setState({
        flag: APP_FLAG,
        user_id: cookie.load("user_id"),
        user_name: cookie.load("user_name"),
      });
    } else {
      this.setState({
        flag: LOGIN_FLAG,
      });
    }
  }

  setGlobalState = (updateGlobalState) => {
    this.setState({
      ...updateGlobalState,
    });
  };

  render() {
    if (this.state.flag === LOGIN_FLAG) {
      return (
        <Login
          global_state={this.setGlobalState}
          state={this.state}
        />
      );
    } else {
      return (
        <App global_state={this.setGlobalState} state={this.state} />
      );
    }
  }
}

import React from 'react';
import ReactDOM from 'react-dom';
import Main from './Main';
import 'antd/dist/antd.css';
import './CSS/index.css';
import { Toaster } from 'react-hot-toast';


ReactDOM.render(
  <React.StrictMode>
    <Main />
    <Toaster />
  </React.StrictMode>,
  document.getElementById('root')
);

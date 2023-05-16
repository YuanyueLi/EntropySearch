import 'antd/dist/reset.css';
import './App.css';
import React, {Suspense} from 'react';
import {BrowserRouter, Routes, Route, Navigate} from "react-router-dom";
import {notification} from 'antd';

import Template from "./Pages/Global/Template";
import MainInput from "./Pages/Input/Main";
import MainResult from "./Pages/Result/Main";
import JobStatus from "./Pages/Global/JobStatus";

function App() {
    return (
        <div className="App">
            <JobStatus/>
            <BrowserRouter>
                <Routes>
                    <Route path="/">
                        <Route index element={
                            <Template><MainInput/></Template>
                        }/>
                        <Route path="result" element={
                            <Template><MainResult/></Template>
                        }/>
                    </Route>
                </Routes>
            </BrowserRouter>
        </div>
    );
}

export default App;

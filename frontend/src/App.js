import 'antd/dist/reset.css';
import './App.css';
import React, {Suspense} from 'react';
import {BrowserRouter, Routes, Route, Navigate} from "react-router-dom";
import {notification} from 'antd';

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
                        <Route index element={<MainInput/>}/>
                        <Route path="result" element={<MainResult/>}/>
                    </Route>
                </Routes>
            </BrowserRouter>
        </div>
    );
}

export default App;

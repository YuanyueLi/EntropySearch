import 'antd/dist/reset.css';
import './App.css';
import React, {Suspense} from 'react';
import {BrowserRouter, Routes, Route, Navigate} from "react-router-dom";
import {notification} from 'antd';

import MainInput from "./Pages/Input/Main";


function App() {
    return (
        <div className="App">
            <BrowserRouter>
                <Routes>
                    <Route path="/">
                        <Route index element={<MainInput/>}/>
                    </Route>
                </Routes>
            </BrowserRouter>
        </div>
    );
}

export default App;

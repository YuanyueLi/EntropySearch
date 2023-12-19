import 'antd/dist/reset.css';
import './App.css';
import React, {Suspense} from 'react';
import {BrowserRouter, Routes, Route, MemoryRouter} from "react-router-dom";

import Template from "./Pages/Global/Template";
import MainInput from "./Pages/Input/Main";
import MainResult from "./Pages/Result/Main";

function App() {
    return (
        <div className="App">
            <MemoryRouter>
                <Routes>
                    <Route index element={
                        <Template><MainInput/></Template>
                    }/>
                    <Route path="result" element={
                        <Template><MainResult/></Template>
                    }/>
                </Routes>
            </MemoryRouter>
        </div>
    );
}

export default App;

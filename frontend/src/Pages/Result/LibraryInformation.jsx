/* global BigInt */
import {Col, Row, Tabs, Space, Table, notification} from 'antd';
import React, {useEffect, useState} from "react";
import {useRequest} from "ahooks";
import axios from "axios";
import {atom, useAtom} from "jotai";

import PlotMolecule from "../../Library/PlotMolecule";
import {atomGlobalLibraryData} from "../Global/Atoms";

const column = [
    {
        title: 'Name',
        dataIndex: 'name',
        key: 'name',
        ellipsis: true,
        width: '30%',
        sorter: (a, b) => a.name.localeCompare(b.name),
        defaultSortOrder: 'ascend',
    }, {
        title: 'Value',
        dataIndex: 'value',
        key: 'value',
        ellipsis: true,
        render: (text) => <div style={{whiteSpace: "pre-line"}}>
            {text}
        </div>

    }]
const capitalizeFirstLetter = (string) => {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


const Main = () => {
    const [stateInfo, setStateInfo] = useState([]);
    const [stateSmiles, setStateSmiles] = useState("");
    const [getAtomGlobalLibraryData,] = useAtom(atomGlobalLibraryData);
    useEffect(() => {
        if (getAtomGlobalLibraryData) {
            const data = {...getAtomGlobalLibraryData};
            delete data['peaks'];
            delete data['num peaks'];
            if (data.smiles) {
                setStateSmiles(data.smiles);
            } else {
                setStateSmiles("");
            }
            let display = Object.entries(data).map(([key, value]) => {
                if (key.startsWith("library-")) {
                    key = key.replace("library-", "")
                }
                if (key in {"_ms_level": 1, "num peaks": 1}) {
                    return {name: capitalizeFirstLetter(key), value: "", key: key}
                }
                return {name: capitalizeFirstLetter(key), value: value, key: key}
            })
            // Filter out the empty value
            display = display.filter((item) => {
                return item.value !== ""
            })
            console.log(display)
            setStateInfo(display);
        } else {
            setStateInfo([]);
            setStateSmiles("");
        }
    }, [getAtomGlobalLibraryData]);

    return <>
        <Row justify={"center"} align={"middle"}>
            <Col>
                {stateSmiles ?
                    <PlotMolecule width={450} height={200} smiles={stateSmiles}/>
                    : <></>}
            </Col>
        </Row>
        <Row>
            <Col span={24}>
                <Table
                    locale={{emptyText: 'Select a item from left to see the information.'}}
                    pagination={false}
                    size={'small'}
                    columns={column} dataSource={stateInfo}/>
            </Col>
        </Row>
    </>
};
export default Main;
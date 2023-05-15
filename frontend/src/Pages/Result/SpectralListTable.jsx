import {Col, Row, Tabs, Space, Table, Tag} from 'antd';
import React, {useEffect, useState, useContext, useMemo} from "react";
import {useNavigate, useLocation} from "react-router-dom";
import {SmileOutlined, FrownOutlined, CheckOutlined} from "@ant-design/icons";
import {useAtom} from "jotai";

import VirtualTable from "../../Library/VirtualTable";
import {useRequest} from "ahooks";
import {atomGlobalRunData, atomSelectedScan, atomGlobalSpectrumData} from "../Global/Atoms";

const columnsTemplate = [
    {
        title: "",
        key: "idx",
        render: (text, record, index) => `${index + 1}`,
        width: 30,
    }, {
        title: "Scan",
        dataIndex: "scan",
        render: (_, record) => record.scan || "NA",
        width: 60,
    }, {
        title: "Name",
        dataIndex: "name",
        render: (_, record) => record.name || "",
        sorter: (a, b) => (a.name || "").localeCompare(b.name || ""),
        width: 50,
    }, {
        title: "RT",
        dataIndex: "rt",
        render: (_, record) => record.rt.toFixed(1),
        width: 50,
    }, {
        title: "Precursor m/z",
        dataIndex: "precursor_mz",
        render: (_, record) => record.precursor_mz.toFixed(3),
        width: 60,
    }, {
        title: "Identity Score",
        dataIndex: "identity_search-score",
        defaultSortOrder: 'descend',
        width: 50,
    }, {
        title: "Open Score",
        dataIndex: "open_search-score",
        width: 50,
    }, {
        title: "NL Score",
        dataIndex: "neutral_loss_search-score",
        width: 50,
    }, {
        title: "Hybrid Score",
        dataIndex: "hybrid_search-score",
        width: 50,
    }];
const columns = columnsTemplate.map(k => ({
    key: k.dataIndex,
    ellipsis: true,
    render: (_, record) => record[k.dataIndex].toFixed(3),
    sorter: (a, b) => (a[k.dataIndex] ?? -1) - (b[k.dataIndex] ?? -1),
    ...k
}));

export default () => {
    const navigate = useNavigate();

    const [stateColumns, setStateColumns] = useState([]);
    const [stateData, setStateData] = useState([]);
    const [stateHighlightRow, setStateHighlightRow] = useState(0);

    const [atomGlobalRun, setAtomGlobalRun] = useAtom(atomGlobalRunData);
    const [atomGlobalSelectedScan, setAtomGlobalSelectedScan] = useAtom(atomSelectedScan);
    const [atomGlobalSpectrum, setAtomGlobalSpectrum] = useAtom(atomGlobalSpectrumData);

    // Update table data
    useEffect(() => {
        if (atomGlobalRun.spectra) {
            const tableData = atomGlobalRun.spectra
            if (tableData) {
                setStateData(tableData.map(d => ({...d, key: d.scan})));
            }
        }
    }, [atomGlobalRun.spectra]);


    return <>
        <VirtualTable
            scrollToRow={stateHighlightRow}
            size={'small'}
            height={500} vid={'spectra-list-table'}
            columns={columns} dataSource={stateData}
            rowClassName={record => {
                // return (atomWikiId.id2 || "").toString() === (record.wiki_id || "").toString() ? 'row-active' : '';
                return ''
            }}
            onRow={record => ({
                onClick: event => {
                    console.log("record", record);
                    setAtomGlobalSelectedScan(record.scan);
                },
            })}
        />
    </>;
};
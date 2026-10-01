import { Col, Row, Tabs, Space, Table, Tag, Spin, Button, Typography, Select } from 'antd';
import { Parser } from '@json2csv/plainjs';
import React, { useEffect, useState, useContext, useMemo } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { SmileOutlined, FrownOutlined, CheckOutlined } from "@ant-design/icons";
import { useAtom } from "jotai";

import VirtualTable from "../../Library/VirtualTable";
import { useRequest } from "ahooks";
import { atomGlobalRunData, atomSelectedScan, atomGlobalSpectrumData } from "../Global/Atoms";

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
        width: 70,
    }, {
        title: "Name",
        dataIndex: "name",
        render: (_, record) => record.name || "",
        sorter: (a, b) => (a.name || "").localeCompare(b.name || ""),
        ellipsis: false,
        width: 200,
    }, {
        title: "RT",
        dataIndex: "rt",
        render: (_, record) => (record.rt === undefined ? -1 : record.rt).toFixed(3),
        width: 50,
    }, {
        title: "Precursor m/z",
        dataIndex: "precursor_mz",
        ellipsis: false,
        render: (_, record) => (record.precursor_mz === undefined ? -1 : record.precursor_mz).toFixed(3),
        width: 80,
    }, {
        title: "Identity Score",
        dataIndex: "identity_search-score",
        defaultSortOrder: 'descend',
        ellipsis: false,
        width: 80,
    }, {
        title: "Open Score",
        dataIndex: "open_search-score",
        ellipsis: false,
        width: 80,
    }, {
        title: "NL Score",
        dataIndex: "neutral_loss_search-score",
        ellipsis: false,
        width: 80,
    }, {
        title: "Hybrid Score",
        dataIndex: "hybrid_search-score",
        ellipsis: false,
        width: 80,
    }];
const baseColumns = columnsTemplate.map(k => ({
    key: k.dataIndex,
    ellipsis: true,
    render: (_, record) => record[k.dataIndex] === undefined ? <Spin /> : record[k.dataIndex].toFixed(3),
    sorter: (a, b) => (a[k.dataIndex] ?? -1) - (b[k.dataIndex] ?? -1),
    ...k
}));

// Fields that already have a dedicated column (or are internal), so we don't
// offer them again in the "extra metadata" picker.
const FIXED_FIELDS = [
    "key", "scan", "name", "rt", "precursor_mz",
    "identity_search-score", "open_search-score", "neutral_loss_search-score", "hybrid_search-score",
];

// Extra metadata can be strings, numbers, arrays etc. so render it defensively.
const formatValue = (v) => {
    if (v === undefined || v === null) return "";
    if (typeof v === "object") return JSON.stringify(v);
    return String(v);
};

export default () => {
    const navigate = useNavigate();

    const [stateColumns, setStateColumns] = useState(null);
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
                setStateData(tableData.map(d => ({ ...d, key: d.scan })));
            }
        }
    }, [atomGlobalRun.spectra]);

    ////////////////////////////////////////////////////////////////////////////////
    // Which extra metadata fields exist on the query spectra, and which of them
    // the user has chosen to show as extra columns.
    const stateAvailableFields = useMemo(() => {
        const fieldSet = new Set();
        stateData.forEach(row => Object.keys(row).forEach(k => fieldSet.add(k)));
        FIXED_FIELDS.forEach(k => fieldSet.delete(k));
        return Array.from(fieldSet).sort();
    }, [stateData]);

    const [stateSelectedFields, setStateSelectedFields] = useState([]);

    // Fixed columns plus one column per selected extra field
    const columns = useMemo(() => [
        ...baseColumns,
        ...stateSelectedFields.map(field => ({
            title: field,
            dataIndex: field,
            key: field,
            ellipsis: true,
            width: 150,
            render: (_, record) => formatValue(record[field]),
            sorter: (a, b) => String(a[field] ?? "").localeCompare(
                String(b[field] ?? ""), undefined, { numeric: true }
            ),
        })),
    ], [stateSelectedFields]);

    const [stateTextFile, setStateTextFile] = useState(null);
    useEffect(() => {
        if (stateData && stateData.length > 0) {
            const parser = new Parser();
            const csv = parser.parse(stateData);
            const data = new Blob([csv], { type: 'text/plain' });
            if (stateTextFile !== null) {
                window.URL.revokeObjectURL(stateTextFile);
            }
            const textFile = window.URL.createObjectURL(data);
            setStateTextFile(textFile);
        }
    }, [stateData]);

    return <>
        <Row justify="end">
            <>
                {
                    stateTextFile ? <>
                        <Button type={"primary"} href={stateTextFile} download="result.csv" >Export results</Button>
                    </> : <></>
                }
            </>
        </Row>
        <Row>
            <Col span={24}>
                <Select
                    mode="multiple"
                    allowClear
                    maxTagCount="responsive"
                    style={{ width: '100%', marginBottom: 8, marginTop: 8 }}
                    placeholder="Add metadata columns"
                    value={stateSelectedFields}
                    onChange={setStateSelectedFields}
                    options={stateAvailableFields.map(f => ({ label: f, value: f }))}
                />
                <VirtualTable
                    scrollToRow={stateHighlightRow}
                    size={'small'}
                    height={500} vid={'spectra-list-table'}
                    columns={columns} dataSource={stateData}
                    rowClassName={record => {
                        return (atomGlobalSelectedScan || "").toString() === (record.key || "").toString() ? 'row-active' : '';
                    }}
                    onRow={record => ({
                        onClick: event => {
                            console.log("record", record);
                            setAtomGlobalSelectedScan(record.key);
                        },
                    })}
                />
            </Col>
        </Row>
    </>;
};
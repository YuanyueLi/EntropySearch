import {Col, Row, Tabs, Space, Table, Tag, Input, Button, Spin, message, notification} from 'antd';
import React, {Suspense, useState, useEffect} from "react";
import {useNavigate, useParams} from "react-router-dom";
import {useAtom} from 'jotai'
import {useRequest} from "ahooks";

import {
    atomGlobalRunData,
    atomSelectedScan,
    atomGlobalSpectrumData,
    atomUpperSpectrumData,
    atomLowerSpectrumData
} from "../Global/Atoms";
import {url} from "../Global/Config";

const Main = () => {
    const [atomGlobalRun, setAtomGlobalRun] = useAtom(atomGlobalRunData);
    const [atomGlobalSelectedScan, setAtomGlobalSelectedScan] = useAtom(atomSelectedScan);
    const [atomGlobalSpectrum, setAtomGlobalSpectrum] = useAtom(atomGlobalSpectrumData);
    const [atomUpperSpectrum, setAtomUpperSpectrum] = useAtom(atomUpperSpectrumData);
    const [atomLowerSpectrum, setAtomLowerSpectrum] = useAtom(atomLowerSpectrumData);

    /////////////////////////////////////////////////////////////////////////////////
    // For debug
    useEffect(() => {
        console.log("atomGlobalRun", atomGlobalRun);
    }, [atomGlobalRun])
    useEffect(() => {
        console.log("atomGlobalSpectrum", atomGlobalSpectrum);
    }, [atomGlobalSpectrum])

    /////////////////////////////////////////////////////////////////////////////////
    // Get data from server
    const getAllSpectra = useRequest(url.getAllSpectra, {
        onSuccess: (result, params) => {
            const data = result.data;
            setAtomGlobalRun({spectra: data});
        }
    });

    const getOneSpectrum = useRequest(url.getOneSpectrum, {
        manual: true,
        onSuccess: (result, params) => {
            const data = result.data;
            setAtomGlobalSpectrum(data);
            setAtomUpperSpectrum({
                precursor_mz: data.precursor_mz,
                peaks: data.peaks
            })
        }
    });

    useEffect(() => {
        console.log("atomGlobalSelectedScan", atomGlobalSelectedScan)
        if (atomGlobalSelectedScan !== null) {
            getOneSpectrum.run(atomGlobalSelectedScan);
        }
    }, [atomGlobalSelectedScan])


    return <></>;
}

export default Main;
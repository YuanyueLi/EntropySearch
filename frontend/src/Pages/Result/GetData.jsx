import {Col, Row, Tabs, Space, Table, Tag, Input, Button, Spin, message, notification} from 'antd';
import React, {Suspense, useState, useEffect} from "react";
import {useNavigate, useParams} from "react-router-dom";
import {useAtom} from 'jotai'
import {useRequest} from "ahooks";

import {
    atomGlobalRunData,
    atomSelectedScan,
    atomGlobalSpectrumData,
    atomSelectedLibrary,
    atomGlobalLibraryData,
    atomUpperSpectrumData,
    atomLowerSpectrumData
} from "../Global/Atoms";
import {atomJobStatus} from "../Global/JobStatus";
import {url} from "../Global/Config";

const Main = () => {
    const [errorNotification, contextHolderErrorNotification] = notification.useNotification();

    const [getAtomGlobalRun, setAtomGlobalRun] = useAtom(atomGlobalRunData);
    const [getAtomGlobalSelectedScan, setAtomGlobalSelectedScan] = useAtom(atomSelectedScan);
    const [getAtomGlobalSpectrum, setAtomGlobalSpectrum] = useAtom(atomGlobalSpectrumData);
    const [getAtomSelectedLibrary, setAtomSelectedLibrary] = useAtom(atomSelectedLibrary);
    const [getAtomGlobalLibrary, setAtomGlobalLibrary] = useAtom(atomGlobalLibraryData);
    const [getAtomUpperSpectrum, setAtomUpperSpectrum] = useAtom(atomUpperSpectrumData);
    const [getAtomLowerSpectrum, setAtomLowerSpectrum] = useAtom(atomLowerSpectrumData);

    /////////////////////////////////////////////////////////////////////////////////
    // For debug
    useEffect(() => {
        console.log("getAtomGlobalRun", getAtomGlobalRun);
    }, [getAtomGlobalRun])
    useEffect(() => {
        console.log("getAtomGlobalSpectrum", getAtomGlobalSpectrum);
    }, [getAtomGlobalSpectrum])

    /////////////////////////////////////////////////////////////////////////////////
    // Get data from server
    const getAllSpectra = useRequest(url.getAllSpectra, {
        onSuccess: (result, params) => {
            const data = result.data;
            setAtomGlobalRun({spectra: data});
        }
    });
    const [getAtomJobStatus] = useAtom(atomJobStatus);
    useEffect(() => {
        if (!getAtomJobStatus.is_running) {
            getAllSpectra.run();
        }
    }, [getAtomJobStatus.is_running])

    const getOneSpectrum = useRequest(url.getOneSpectrum, {
        manual: true,
        onSuccess: (result, params) => {
            const data = result.data;
            console.log("getOneSpectrum", data)
            if(data.is_error){
                errorNotification.error({
                    message: 'Error',
                    description: data.status,
                    duration: 0,
                    placement: "top",
                });
                return;
            }
            setAtomGlobalSpectrum(data);
            setAtomUpperSpectrum({
                precursor_mz: data.precursor_mz,
                peaks: data.peaks
            })
            setAtomLowerSpectrum({
                precursor_mz: null,
                peaks: null
            })
        }
    });

    const getOneLibrarySpectrum = useRequest(url.getOneLibrarySpectrum, {
        manual: true,
        onSuccess: (result, params) => {
            const data = result.data;
            if(data.is_error){
                errorNotification.error({
                    message: 'Error',
                    description: data.status,
                    duration: 0,
                    placement: "top",
                });
                return;
            }
            console.log("getLibrarySpectrum", data)
            setAtomGlobalLibrary(data);
            setAtomLowerSpectrum({
                precursor_mz: data.precursor_mz,
                peaks: data.peaks
            })
        }
    });
    useEffect(() => {
        if (getAtomSelectedLibrary.charge !== null && getAtomSelectedLibrary.idx !== null) {
            getOneLibrarySpectrum.run(getAtomSelectedLibrary.charge, getAtomSelectedLibrary.idx);
        }
    }, [getAtomSelectedLibrary])

    useEffect(() => {
        console.log("getAtomGlobalSelectedScan", getAtomGlobalSelectedScan)
        if (getAtomGlobalSelectedScan !== null) {
            getOneSpectrum.run(getAtomGlobalSelectedScan);
        }
    }, [getAtomGlobalSelectedScan])


    return <>
        {contextHolderErrorNotification}
    </>;
}

export default Main;
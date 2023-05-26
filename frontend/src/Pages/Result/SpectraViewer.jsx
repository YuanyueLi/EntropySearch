import {Col, Row, Tabs, Space, Table, Tag} from 'antd';
import React, {useEffect, useState, useContext} from "react";
import {useAtom} from "jotai";

import PlotSpectrum from "../../Library/PlotSpectrum";
import {atomUpperSpectrumData, atomLowerSpectrumData} from "../Global/Atoms";


const SpectraViewer = () => {
    const [statePlot, setStatePlot] = useState({
        specA: {
            precursorMz: null,
            peaks: null
        },
        specB: {
            precursorMz: null,
            peaks: null
        }
    });

    const [getAtomUpperSpectrumData, setAtomUpperSpectrumData] = useAtom(atomUpperSpectrumData);
    const [getAtomLowerSpectrumData, setAtomLowerSpectrumData] = useAtom(atomLowerSpectrumData);
    useEffect(() => {
        const upperSpectrum = getAtomUpperSpectrumData || {};
        const lowerSpectrum = getAtomLowerSpectrumData || {};
        setStatePlot({
            specA: {
                precursorMz: upperSpectrum.precursor_mz,
                peaks: upperSpectrum.peaks
            },
            specB: {
                precursorMz: lowerSpectrum.precursor_mz,
                peaks: lowerSpectrum.peaks
            }
        });
    }, [getAtomUpperSpectrumData, getAtomLowerSpectrumData]);

    return <>
        <Row justify={"center"}>
            <Col span={24}>
                <PlotSpectrum
                    data={statePlot} height={"450px"}/>
            </Col>
        </Row>
    </>
};
export default SpectraViewer;
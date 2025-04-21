import React, {useEffect, useRef, useState} from 'react';
import {Row, Col, Tabs} from 'antd';
import Plot from 'react-plotly.js';

const funcCheckPeaks = (peaks) => {
    if (peaks) {
        peaks.sort((a, b) => b[1] - a[1])
        const peaks_new = peaks.slice(0, 1000)
        peaks_new.sort((a, b) => a[0] - b[0])
        // console.log(peaks_new)
        return peaks_new
    } else {
        return peaks
    }
}

const funcNormalizeSpec = (precursorMz, peaks) => {
    const intensityMax = Math.max.apply(Math, peaks.map((p) => p[0] < precursorMz - 1.6 ? p[1] : 0))
    if (intensityMax > 0) {
        peaks = peaks.map(p => [p[0], p[1] / intensityMax])
    }
    return peaks
}

const funcGenerateNeutralLoss = (precursorMz, peaks) => {
    let zeroMz = 0.
    if (precursorMz) {
        zeroMz = precursorMz
    }
    return peaks.map(p => [p[0] - zeroMz, p[1]])
}

const funcPlotSpectrum = (plotData) => {
    const precursorMzA = plotData.specA.precursorMz
    const precursorMzB = plotData.specB.precursorMz
    const peaksA = funcCheckPeaks(plotData.specA.peaks)
    const peaksB = funcCheckPeaks(plotData.specB.peaks)
    const plotType = plotData.plotType || "normal" // "normal" or "neutral_loss"

    // console.log(plotData)
    // Normalize spectrum: if only one spectrum is available, do not normalize.
    let spectrumUp, spectrumDown
    let plotComparisonSpec;
    if (peaksB) {
        plotComparisonSpec = true
        if (peaksA) {
            spectrumUp = funcNormalizeSpec(precursorMzA, peaksA)
            spectrumDown = funcNormalizeSpec(precursorMzB, peaksB)
        } else {
            spectrumUp = []
            spectrumDown = peaksB
        }
    } else {
        plotComparisonSpec = false
        spectrumUp = peaksA
    }
    let plotAllPeaks = []
    // If plotType is "neutral_loss", generate neutral loss peaks for plot
    if (plotType === "neutral_loss") {
        spectrumUp = funcGenerateNeutralLoss(precursorMzA, spectrumUp)
        if (plotComparisonSpec) {
            spectrumDown = funcGenerateNeutralLoss(precursorMzB, spectrumDown)
        }
    }

    // Add peaks to plot
    for (let peak of spectrumUp) {
        plotAllPeaks.push({
            x0: peak[0], x1: peak[0],
            y0: 0, y1: peak[1],
            line: {color: "#8884d8", width: 1}, type: 'line'
        })
    }
    let data = [{
        x: spectrumUp.map((x) => x[0]),
        y: spectrumUp.map((x) => x[1]),
        hovertemplate: "m/z: %{x}<br>" +
            "Intensity: %{y}<extra></extra>", showlegend: false,
        mode: 'markers', type: 'scatter',
        hoverlabel: {bgcolor: "#FFF"}, marker: {color: "#8884d8", size: 0.1},
    }]

    if (plotComparisonSpec) {
        for (let peak of spectrumDown) {
            plotAllPeaks.push({
                x0: peak[0], x1: peak[0],
                y0: 0, y1: -peak[1],
                line: {color: "#d88484", width: 1}, type: 'line'
            })
        }
        data.push(
            {
                x: spectrumDown.map((x) => x[0]),
                y: spectrumDown.map((x) => -x[1]),
                hovertemplate: "m/z: %{x}<br>Intensity: %{y}<extra></extra>",
                showlegend: false, mode: 'markers', type: 'scatter',
                hoverlabel: {bgcolor: "#FFF"}, marker: {color: "#8884d8", size: 0.1},
            }
        )
    }

    // Calculate figure's size
    let xMin, xMax, yMin, yMax
    xMin = 0;
    if (plotComparisonSpec) {
        xMax = 1.05 * Math.max(...(spectrumUp.map(x => x[0])), ...(spectrumDown.map(x => x[0])),
            precursorMzA, precursorMzB)
        yMax = 1.2
        yMin = -1.2
    } else {
        xMax = 1.05 * Math.max(...(spectrumUp.map(x => x[0])), precursorMzA)
        yMax = 1.2 * Math.max(...(spectrumUp.map(x => x[0] < precursorMzA - 1.6 ? x[1] : 0)))
        yMin = 0
        yMax = yMax <= 0 ? 1.2 * Math.max(...(spectrumUp.map(x => x[1]))) : yMax
    }
    if (plotType === "neutral_loss") {
        if (plotComparisonSpec) {
            xMin = 1.05 * Math.min(...(spectrumUp.map(x => x[0])), ...(spectrumDown.map(x => x[0])), -1)
            xMax = 1.05 * Math.max(...(spectrumUp.map(x => x[0])), ...(spectrumDown.map(x => x[0])), 0.05 * Math.abs(xMin))
        } else {
            xMin = 1.05 * Math.min(...(spectrumUp.map(x => x[0])), -1)
            xMax = 1.05 * Math.max(...(spectrumUp.map(x => x[0])), 0.05 * Math.abs(xMin))
        }
    }

    // Add precursor ion
    if (precursorMzA && !isNaN(precursorMzA)) {
        plotAllPeaks.push({
            x0: precursorMzA, x1: precursorMzA,
            y0: 0, y1: yMax,
            type: 'line', line: {color: 'black', width: 1, dash: 'dot'}
        })
    }
    if (precursorMzB && !isNaN(precursorMzB)) {
        plotAllPeaks.push({
            x0: precursorMzB, x1: precursorMzB,
            y0: 0, y1: yMin,
            type: 'line', line: {color: 'black', width: 1, dash: 'dot'}
        })
    }

    // Set layout
    let layout = {
        xaxis: {title: {text: 'm/z',}, range: [xMin, xMax]},
        yaxis: {title: {text: 'Intensity',}, range: [yMin, yMax]},
        autosize: true,
        hovermode: "closest",
        shapes: plotAllPeaks,
        margin: {l: 55, r: 10, b: 30, t: 10, pad: 0},
    };
    if (plotComparisonSpec) {
        layout.yaxis.title.text = 'Normalized intensity'
    }
    const config = {
        responsive: true,
        scrollZoom: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'zoom2d', 'pan2d'],
        toImageButtonOptions :{format:"svg"},
    }
    return {data: data, layout: layout, config: config}
}

const PlotSpectrum = (props) => {
    // Deal with loading
    const [stateLoading, setLoading] = useState(true)
    useEffect(() => {
        setLoading(props.loading)
    }, [props.loading])

    // Display mode
    const [stateDisplayMode, setDisplayMode] = useState("normal")

    const [stateData, setData] = useState({
        data: [], layout: {}, config: {}
    })
    useEffect(() => {
        const data = {plotType: stateDisplayMode, ...props.data}
        if (!data.specA) {
            data.specA = {}
        }
        if (!data.specB) {
            data.specB = {}
        }
        if (data.specA.peaks || data.specB.peaks) {
            const dataPlot = funcPlotSpectrum(data)
            // if (props.height) {
            //     dataPlot.layout.height = props.height
            // }
            setData(dataPlot)
        }
    }, [props.data, stateDisplayMode])

    const [stateRevision, setStateRevision] = useState(0);
    useEffect(() => {
        setStateRevision(stateRevision + 1)
    }, [])

    // useEffect(() => {
    //     console.log(stateData)
    // }, [stateData])
    return (
        <div>
            <Tabs defaultActiveKey="normal" centered onChange={(k) => setDisplayMode(k)}
                  items={[
                      {key: "normal", label: "Normal"},
                      {key: "neutral_loss", label: "Neutral loss"},
                  ]}/>
            <Row>
                <Col style={{height: props.height}}>
                    {stateLoading ? <></> :
                        <Plot
                            style={{position: 'relative', width: '100%', height: '100%'}}
                            useResizeHandler={true}
                            revision={stateRevision}
                            data={stateData.data} layout={stateData.layout} config={stateData.config}/>
                    }
                </Col>
            </Row>
        </div>
    )
}

export default PlotSpectrum;
import React, {Suspense, useEffect} from "react";
import {useNavigate, useLocation} from "react-router-dom";
import {Col, Row, Skeleton, Steps} from "antd";
import {atom, useAtom} from 'jotai'
import JobStatus, {atomJobStatus} from "./JobStatus";


const TemplateWebsite = (props) => {
    let navigate = useNavigate();
    const location = useLocation();

    const [jobStatus, setJobStatus] = useAtom(atomJobStatus);
    return (<>
        <JobStatus/>
        <Row justify="space-between" align={"middle"} style={{background: "#f5f5f5"}}>
            <Col span={8} style={{paddingLeft: "24px", paddingRight: "24px"}}>
                <h1 onClick={() => navigate('/')}
                    style={{
                        cursor: "pointer",
                        lineHeight: 1.5,
                        color: "#5f9bf1",
                        paddingLeft: "8px",
                        marginBottom: 0,
                    }}>Flash Entropy Search</h1>
            </Col>
            <Col span={8} style={{paddingLeft: "24px", paddingRight: "24px"}}>
                <Steps current={{'/': 0, '/result': 1}[location.pathname]}
                       size="small" type={"navigation"}
                       onChange={(current) => {
                           if (current === 0) navigate('/')
                           else if (current === 1) navigate('/result')
                       }}
                       items={[
                           {title: 'Set parameters', disabled: jobStatus.is_running, key: 0},
                           {title: 'View result', disabled: !jobStatus.is_ready, key: 1},
                       ]}
                />
            </Col>
            <Col span={8} style={{paddingLeft: "24px", paddingRight: "24px"}}>
                <div style={{paddingRight: "24px"}}>
                    {/*<UserInfo/>*/}
                </div>
            </Col>
        </Row>
        <div style={{paddingTop: "8px"}}/>
        <Suspense fallback={<div>Loading...<Skeleton active/></div>}>
            {props.children}
        </Suspense>
    </>);
}
export default TemplateWebsite;
import {useState, useEffect} from "react";
import {Space, Row, Col, Spin, Modal, Card, Button} from 'antd';
import {UploadOutlined} from '@ant-design/icons';
import {useRequest} from 'ahooks';
import {url} from "../Global/Config";
import InputParameters from "./InputParameters";
import {atomJobStatus} from "../Global/JobStatus";
import {atom, useAtom} from "jotai";
import {useNavigate, useParams} from "react-router-dom";

export const atomShowModalInfo = atom(false);
const ModalInfo = () => {
    const [jobStatus, setJobStatus] = useAtom(atomJobStatus);
    const [showModalInfo, setShowModalInfo] = useAtom(atomShowModalInfo);

    const navigate = useNavigate();

    return <Modal title={<><br/></>} open={showModalInfo} footer={null}
                  closable={false} keyboard={false} maskClosable={false}
                  onOk={() => setShowModalInfo(false)} onCancel={() => setShowModalInfo(false)}>
        <Row align={"middle"} justify={"center"}>
            <Col span={24}>
                {jobStatus.status ? <>
                    <Space align={"baseline"}>
                        <Spin/> <>{jobStatus.status}</>
                    </Space>
                </> : <>
                    <></>
                </>}
            </Col>
        </Row>
        <br/>
        <Row align={"middle"} justify={"center"}>
            <Col span={24}>
                <>{jobStatus.is_finished ? <>
                    <p>Spectral search has been finished. You can view the results now. </p>
                </> : <>{jobStatus.is_ready ? <>
                    <p>Spectral search hasn't been finished yet, but you can still view part of the results now.</p>
                </> : <></>}</>}
                </>
            </Col>
        </Row>
        <Row align={"middle"} justify={"center"}>
            {jobStatus.is_ready || jobStatus.is_finished ? <>
                <Button type="primary" onClick={() => {
                    setShowModalInfo(false)
                    navigate("/result")
                }}>  View results</Button>
            </> : <></>}
        </Row>
    </Modal>
}

const Main = () => {
    return <div>
        <ModalInfo/>
        <Row align={"middle"} justify={"center"}>
            <Col span={24}>
                <br/>
                <Card style={{width: 800, height: 500, margin: "auto"}}>
                    <Row align={"middle"} justify={"center"} style={{height: "100%"}}>
                        <Col span={24}>
                            <InputParameters/>
                        </Col>
                    </Row>
                </Card>
            </Col>
        </Row>
    </div>
};

export default Main;
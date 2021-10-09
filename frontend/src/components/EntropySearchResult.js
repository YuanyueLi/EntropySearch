import {useState} from "react";
import {Button, Input, Row, Col, Modal} from 'antd';
import {useRequest} from 'ahooks';
import {useHistory} from "react-router-dom";


const serverAddress = "http://localhost:8765"
const EntropySearchResult = () => {
    const history = useHistory();
    const [stateOutput, setOutput] = useState("")
    const [stateRunning, setRunning] = useState(true)
    const postGetResult = useRequest((data) => ({
        url: serverAddress + "/get_result", method: 'post', body: JSON.stringify(data)
    }), {
        pollingInterval: 1000,
        onSuccess: (result, params) => {
            if (result.is_finished) {
                postGetResult.cancel()
                setRunning(false)
                Modal.success({
                    title: "Finished!",
                    centered: true
                })
            }
            console.log(result)
            setOutput(result.output)
        }
    })

    return <>
        <Row justify={"center"}>
            <Col span={22}>
                <Row>
                    <Col>Output:</Col>
                </Row>
                <Row justify={"center"}>
                    <Col span={24}>
                        <Input.TextArea style={{height: "450px"}}
                                        value={stateOutput}/>
                    </Col>
                </Row>
                <br/>
                <Row justify={"center"}>
                    <Col span={2}>
                        <Button type="primary" disabled={stateRunning}
                                onClick={() => history.push("/parameter")}>
                            {stateRunning ? "Running" : "Search another file"}
                        </Button>
                    </Col>
                </Row>
            </Col>
        </Row>
    </>
}

export default EntropySearchResult;
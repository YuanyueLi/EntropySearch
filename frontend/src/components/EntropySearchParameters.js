import {useState, useEffect} from "react";
import {Upload, Button, Form, Input, InputNumber, Row, Col, ConfigProvider, Modal} from 'antd';
import {UploadOutlined} from '@ant-design/icons';
import {useRequest} from 'ahooks';
import {useHistory} from "react-router-dom";


const serverAddress = "http://localhost:8765"

const EntropySearchParameters = () => {
    const history = useHistory();
    const [form] = Form.useForm();
    const defaultValues = {
        file_search: "",
        file_library: "",
        file_output: "",
        ms1_ppm: 10,
        ms2_da: 0.05,
        noise: 0.01,
        precursor_removal: 1.6,
        score_min: 0.5,
        threads: 1
    }
    const formStyle2 = {
        labelCol: {span: 16}, wrapperCol: {span: 2}
    }
    const validateMessages = {
        required: "Please input '${label}'",
    };
    const [stateEnableFinish, setEnableFinish] = useState(true)

    const postSearchParameter = useRequest((data) => {
        return {
            url: serverAddress + "/entropy_search_parameter", method: 'post', body: JSON.stringify(data)
        }
    }, {
        manual: true,
        onSuccess: (result, params) => {
            console.log(result)
        },
        onError: () => {
            Modal.error({
                title: "Error!",
                centered: true
            })
        }
    });

    const onFinish = (values) => {
        //console.log('Success:', values);
        setEnableFinish(false)
        postSearchParameter.run(values)
        history.push("/result")
    };

    return <>
        <Row align={"middle"} justify={"center"}>
            <Col span={22}>
                <ConfigProvider form={{validateMessages}}>
                    <Form name="basic" form={form}
                          labelCol={{span: 5}} wrapperCol={{span: 18}}
                          initialValues={defaultValues}
                          onFinish={onFinish}
                          autoComplete="off"
                          requiredMark={false}>
                        <Form.Item label={"Spectral file to search"} name="file_search"
                                   rules={[{required: true}]}>
                            <InputFile fileFormat={".msp,.mzML,.mzML.gz"}
                                       placeholder={"The file you want to analyze."}
                                       onChange={(e) => {
                                           let result = e
                                           if (e.lastIndexOf('.')) {
                                               result = e.substr(0, e.lastIndexOf('.'))
                                           }
                                           form.setFieldsValue({file_output: result + ".result.csv"})
                                       }}/>
                        </Form.Item>
                        <Form.Item label={"Spectral library"} name="file_library"
                                   rules={[{required: true}]}>
                            <InputFile fileFormat={".msp"}
                                       placeholder={"Public library can be downloaded from https://MassBank.us"}/>
                        </Form.Item>
                        <Form.Item label={"Result file"} name={"file_output"} required
                                   rules={[{required: true}]}>
                            <Input/>
                        </Form.Item>
                        <Form.Item label={"Minimum similarity score needed for report"} name={"score_min"}
                                   {...formStyle2}>
                            <InputNumber min={0} max={1} step={0.1}/>
                        </Form.Item>
                        <Form.Item label={"Remove ions have m/z higher then precursor m/z minus this value"}
                                   name={"precursor_removal"}
                                   {...formStyle2}>
                            <InputNumber step={0.1}/>
                        </Form.Item>
                        <Form.Item label={"Precursor m/z tolerance (in ppm)"} name={"ms1_ppm"}
                                   {...formStyle2}>
                            <InputNumber min={0} step={10}/>
                        </Form.Item>
                        <Form.Item label={"Product ions m/z tolerance (in Da)"} name={"ms2_da"}
                                   {...formStyle2}>
                            <InputNumber min={0} step={0.1}/>
                        </Form.Item>
                        <Form.Item label={"Noise removed before spectra search"} name={"noise"}
                                   {...formStyle2}>
                            <InputNumber min={0} max={1} step={0.1}/>
                        </Form.Item>
                        <Form.Item label={"Threads used for search"} name={"threads"}
                                   {...formStyle2}>
                            <IntegerInputNumber min={1} disabled/>
                        </Form.Item>
                        <Form.Item wrapperCol={{offset: 10, span: 4}}>
                            <Button type="primary" htmlType="submit" disabled={!stateEnableFinish}>
                                Start
                            </Button>
                        </Form.Item>
                    </Form>
                </ConfigProvider>
            </Col>
        </Row>
    </>
}

const FileSelector = (props) => {
    const uploadProps = {
        multiple: false,
        maxCount: 1,
        showUploadList: false,
        accept: props.fileFormat,
        beforeUpload: (file) => {
            if (file) {
                if (file.path) {
                    props.setFile(file.path)
                } else {
                    props.setFile(file.name)
                }
            }
            return false
        },
    }

    return <>
        <Upload {...uploadProps}>
            <Button icon={<UploadOutlined/>}>Select file</Button>
        </Upload>
    </>
}

const InputFile = ({value = undefined, onChange, fileFormat, placeholder}) => {
    const [stateFilePath, setFilePath] = useState(value)

    useEffect(() => {
        //console.log(stateFilePath)
        if (stateFilePath) {
            onChange?.(stateFilePath)
        }
    }, [stateFilePath, onChange])

    return <Row justify={"space-between"}>
        <Col span={19}>
            <Input onChange={(e) => setFilePath(e.target.value)} value={stateFilePath} placeholder={placeholder}/>
        </Col>
        <Col span={4}>
            <FileSelector setFile={setFilePath} fileFormat={fileFormat}/>
        </Col>
    </Row>
}

const IntegerInputNumber = (props) => {
    const {defaultValue, min, placeholder} = props;
    const [preValue, setPreValue] = useState(defaultValue ?? min ?? 0);

    const handleChange = (value) => {
        setPreValue(value);
    };

    const formatter = (value) => value;

    const parse = (value) => {
        if (value === "") {
            return value;
        }

        if (
            Number.isNaN(Number.parseInt(value, 10)) ||
            Number(value) === 0 ||
            Number(value) < min
        ) {
            return preValue;
        }

        return Math.abs(Number.parseInt(value, 10));
    };

    const handleBlur = ({target: {value}}) => {
        if (value === "") {
            setPreValue(defaultValue);
        }
    };

    return <InputNumber
        min={min}
        step={1}
        value={preValue}
        defaultValue={defaultValue}
        placeholder={placeholder}
        formatter={formatter}
        parser={parse}
        onChange={handleChange}
        onBlur={handleBlur}
        {...props}
    />
}


export default EntropySearchParameters;
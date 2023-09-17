import {useState, useEffect} from "react";
import {Upload, Button, Form, Input, InputNumber, Row, Col, ConfigProvider, Modal, Tooltip} from 'antd';
import {UploadOutlined} from '@ant-design/icons';
import {useRequest} from 'ahooks';
import {url} from "../Global/Config";
import {useAtom} from "jotai";
import {atomShowModalInfo} from "./Main";

const InputParameters = (showNext) => {
    const [, setShowModalInfo] = useAtom(atomShowModalInfo);
    const [form] = Form.useForm();
    const defaultValues = {
        // file_query: "/p/FastEntropySearch/gui/test/input/query.msp",
        // file_library: "/p/FastEntropySearch/gui/test/input/query.msp",
        file_query: "",
        file_library: "",
        path_output: "/p/FastEntropySearch/gui/test/output/",
        charge: 0,
        ms1_tolerance_in_da: 0.01,
        ms2_tolerance_in_da: 0.02,
        top_n: 100,
        score_min: 0.5,
        cores: 1
    }
    const formStyle2 = {
        labelCol: {span: 16}, wrapperCol: {span: 8}
    }
    const validateMessages = {
        required: "Please input '${label}'",
    };
    const [stateEnableFinish, setEnableFinish] = useState(true)

    // // Update CPU cores
    // const getCpuCores = useRequest(url.getCpuCores, {
    //     onSuccess: (result, params) => {
    //         const data = result.data
    //         form.setFieldsValue({cores: data.cpu})
    //     }
    // })

    const postSearchParameter = useRequest(url.startEntropySearch, {
        manual: true,
        onSuccess: (result, params) => {
            console.log(result)
            console.log(showNext)
            setShowModalInfo(true)
        },
        onError: (data) => {
            console.log(data)
            Modal.error({
                title: "Error!",
                centered: true
            })
        }
    });

    const onFinish = (values) => {
        console.log('Success:', values);
        setEnableFinish(false)
        postSearchParameter.run(values)
    };

    return <>
        <br/>
        <Row align={"middle"} justify={"center"}>
            <Col span={22}>
                <ConfigProvider form={{validateMessages}}>
                    <Form name="basic" form={form}
                          labelCol={{span: 5}} wrapperCol={{span: 18}}
                          initialValues={defaultValues}
                          onFinish={onFinish}
                          autoComplete="off"
                          requiredMark={false}>
                        <Form.Item label={"Spectral file to search"} name="file_query"
                                   rules={[{required: true}]}>
                            <InputFile fileFormat={".msp,.mzML,.mgf"}
                                       placeholder={"The mzML, mgf, msp format is supported."}
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
                            <InputFile fileFormat={".msp,.mgf,.mzML,.lbm2,.esi"}
                                       placeholder={"The msp, lbm2, esi, mgf, mzML is supported."}/>
                        </Form.Item>
                        {/*<Form.Item label={"Result file"} name={"file_output"} required*/}
                        {/*           rules={[{required: true}]}>*/}
                        {/*    <Input/>*/}
                        {/*</Form.Item>*/}
                        <Tooltip title={"1 means all input spectra have charge +1, -1 means all input spectra have charge -1, 0 means auto-detection charge from input file."}>
                            <Form.Item label={"Charge"} name={"charge"} {...formStyle2}>
                                    <InputNumber min={-10} step={1}/>
                            </Form.Item>
                        </Tooltip>
                        <Form.Item label={"Report top n hits"} name={"top_n"}
                                   {...formStyle2}>
                            <InputNumber min={1} step={10}/>
                        </Form.Item>
                        <Form.Item label={"Precursor m/z tolerance (in Da)"} name={"ms1_tolerance_in_da"}
                                   {...formStyle2}>
                            <InputNumber min={0.0001} step={0.01}/>
                        </Form.Item>
                        <Form.Item label={"Product ions m/z tolerance (in Da)"} name={"ms2_tolerance_in_da"}
                                   {...formStyle2}>
                            <InputNumber min={0.0001} step={0.01}/>
                        </Form.Item>
                        <Form.Item label={"Threads used for search"} name={"cores"}
                                   {...formStyle2}>
                            <IntegerInputNumber min={1} step={1}/>
                        </Form.Item>
                        <Form.Item wrapperCol={{offset: 10, span: 4}}>
                            <Button type="primary" htmlType="submit">
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

export default InputParameters;
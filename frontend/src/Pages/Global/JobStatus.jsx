import React, {Suspense, useState, useEffect} from "react";
import {atom, useAtom} from 'jotai'
import {message} from "antd";
import {useRequest} from "ahooks";
import {url} from "../Global/Config";

export const atomJobStatus = atom({
    status: "", is_ready: false, is_finished: false,
})


const JobStatus = () => {
    const [jobStatus, setJobStatus] = useAtom(atomJobStatus)
    const [messageApi, contextHolder] = message.useMessage();

    const getJobStatus = useRequest(url.getStatus, {
        pollingInterval: 1000,
        onSuccess: (result, params) => {
            const data = result.data;
            setJobStatus(data)
            if (!(data.is_ready && data.is_finished)) {
                // message.info(data.status, 1)
                messageApi.open({
                    key: "jobStatus",
                    content: data.status,
                    type: "loading",
                })
            }
        }
    })

    useEffect(() => {
        getJobStatus.run()
    }, [])

    useEffect(() => {
        console.log(jobStatus)
    }, [jobStatus])

    return <>
        {contextHolder}
    </>
}

export default JobStatus;
import React, {Suspense, useState, useEffect} from "react";
import {atom, useAtom} from 'jotai'
import {message, notification, Spin, Space} from "antd";
import {useRequest} from "ahooks";
import {url} from "../Global/Config";

export const atomJobStatus = atom({
    status: "", is_ready: false, is_running: false, is_error: false
})


const JobStatus = () => {
    const [jobStatus, setJobStatus] = useAtom(atomJobStatus)
    const [messageApi, contextHolder] = message.useMessage();
    const [errorNotification, contextHolderErrorNotification] = notification.useNotification();

    const getJobStatus = useRequest(url.getStatus, {
        pollingInterval: 1000,
        onSuccess: (result, params) => {
            errorNotification.destroy("jobStatus")
            const data = result.data;
            setJobStatus(data)
            if (data.is_running) {
                messageApi.open({
                    key: "jobStatus",
                    content: data.status,
                    type: "loading",
                })
            }
            if (data.is_error) {
                errorNotification.error({
                    key: "runningError",
                    message: "Error",
                    description: data.status,
                    duration: 0,
                    placement: "top",
                })
            }
            // if ((data.is_ready && (!data.is_finished)) || (!data.is_ready && data.is_finished)) {
            //     // message.info(data.status, 1)
            //     messageApi.open({
            //         key: "jobStatus",
            //         content: data.status,
            //         type: "loading",
            //     })
            // }
        },
        onError: (error, params) => {
            console.log(error)
            errorNotification.info({
                key: "jobStatus",
                message: "Software is busy",
                description: <><Space><Spin/>Connecting to the backend...</Space><br/>This may take up to 10 minutes for the first time startup.</>,
                duration: 0,
                placement: "top",
            })
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
        {contextHolderErrorNotification}
    </>
}

export default JobStatus;
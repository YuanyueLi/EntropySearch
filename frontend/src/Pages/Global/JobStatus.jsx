import React, {Suspense, useState, useEffect} from "react";
import {atom, useAtom} from 'jotai'
import {useRequest} from "ahooks";
import {url} from "../Global/Config";

export const atomJobStatus = atom({
    status: "", is_ready: false, is_finished: false,
})

const JobStatus = () => {
    const [jobStatus, setJobStatus] = useAtom(atomJobStatus)
    const getJobStatus = useRequest(url.getStatus, {
        pollingInterval: 10000,
        onSuccess: (result, params) => {
            setJobStatus(result.data)
        }
    })

    useEffect(() => {
        getJobStatus.run()
    }, [])

    useEffect(() => {
        console.log(jobStatus)
    }, [jobStatus])

    return <>
    </>
}

export default JobStatus;
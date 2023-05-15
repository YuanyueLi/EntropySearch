import {Col, Row, Tabs, Space, Table, Tag, Input, Button, Spin, Card} from 'antd';
import React, {Suspense, useState, useEffect} from "react";
import {useNavigate, useParams} from "react-router-dom";
import {useAtom} from 'jotai'

import TemplateCard from "../../Library/TemplateCard";
import SpectralListTable from "./SpectralListTable";
import GetData from "./GetData";
import SpectraViewer from "./SpectraViewer";

const Main = () => {
    const navigate = useNavigate();

    return <>
        <GetData/>
        <br/>
        <Row justify={"center"} gutter={[16, 16]} style={{marginRight: 0, marginLeft: 0}}>
            <Col xs={24} sm={24} md={24} lg={15}>
                <TemplateCard card_id={'card-search_result'} card_title={'Entropy search results'}>
                    <SpectralListTable/>
                </TemplateCard>
            </Col>
            <Col xs={24} sm={24} md={24} lg={9}>
                <TemplateCard card_id={'card-spectra_viewer'} card_title={'Spectra Viewer'}>
                    <SpectraViewer/>
                </TemplateCard>
                <br/>
                <TemplateCard card_id={'card-library_information'} card_title={'Library information'}>
                    LibraryInformation
                </TemplateCard>
            </Col>
        </Row>
        <br/>
    </>;
}

export default Main;
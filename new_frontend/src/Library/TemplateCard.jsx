import React from 'react';
import {Collapse, Card} from 'antd';


function TemplateCard(props) {
    let defaultActiveKey = props.card_id
    if (props.noActive) {
        defaultActiveKey = null
    }
    return (
        <div>
            <Card hoverable style={{cursor: "default"}} headStyle={{cursor: "default"}} bodyStyle={{padding: 0}}>
                <Collapse defaultActiveKey={defaultActiveKey}
                          style={{borderLeft: 0, borderRight: 0, borderTop: 0}}
                          {...props}>
                    <Collapse.Panel header={<>{props.card_title}</>} key={props.card_id}
                                    style={{borderTop: 0, borderBottom: 0, padding: 0}}>
                        {props.children}
                    </Collapse.Panel>
                </Collapse>
            </Card>
        </div>
    )
}


export default TemplateCard
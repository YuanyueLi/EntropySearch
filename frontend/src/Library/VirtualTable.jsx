import React, {useEffect, useMemo} from "react";
import {Table} from 'antd';
import {scrollTo, VList} from 'virtuallist-antd'

const VirtualTable = (props) => {
    useEffect(() => {
        if (props.scrollToRow && props.scrollToRow > 0) {
            setTimeout(() => {
                // console.log("ScrollTo", {row: props.scrollToRow, vid: props.vid})
                scrollTo({row: props.scrollToRow, vid: props.vid});
            }, 2000);
        }
    }, [props.scrollToRow]);
    return <Table {...props}
                  pagination={false}
                  components={useMemo(() => {
                      return VList({
                          height: props.height,
                          resetTopWhenDataChange: false,
                          vid: props.vid || 'virtual-table',
                      })
                  }, [])}
                  scroll={{y: props.height}}/>
}
export default VirtualTable;

import React, {useRef, useEffect, useContext} from 'react';

function PlotMolecule(props) {
    const refPlot = useRef(null)
    useEffect(() => {
        // console.log(props.smiles)
        import('smiles-drawer').then(SmilesDrawer => {
            if (props.smiles && props.smiles.length > 0 && refPlot.current) {
                let option = {
                    width: props.width,
                    height: props.height,
                }
                let smilesDrawer = new SmilesDrawer.Drawer(option)

                SmilesDrawer.parse(props.smiles, function (tree) {
                    smilesDrawer.draw(tree, refPlot.current, "light", false)
                }, function (err) {
                    console.log("Error in plot molecule:", err, props.smiles)
                })
            }
        })
    }, [props.smiles])

    return (
        <canvas ref={refPlot}  width={props.width} height={props.height} {...props}/>
    )
}

export default PlotMolecule
import {React, useEffect, useRef, Children} from 'react'

export default function Modal({children, onClose, open, title, noCloseButton=false}) {
	// var toFocus = []
	// const elementToFocus = useRef(null)
	// useEffect(() => {
	// 	if(elementToFocus.current){
	// 	console.log(elementToFocus)
	// 	elementToFocus.current.focus()}
	// }, [open])
	return (
		<div className="modal" style={open?{opacity:1, transform:"none", pointerEvents:"all"}:{opacity:0, transform:"scale(0.8)", pointerEvents:"none"}}>
			<h1 style={{marginTop:0}}>{title}</h1>
			{/* {Children.map(children, (child)=>{
				if(child.props.focusthis) child.props.ref=elementToFocus
				return child
			})} */}
			{children}
            {(!noCloseButton)&&(
				<button className="hoverfancy" style={{"position":"absolute","top":"16px","right":"16px","width":"48px","height":"48px","display":"flex","WebkitAlignItems":"center","WebkitBoxAlign":"center","msFlexAlign":"center","alignItems":"center","WebkitBoxPack":"center","WebkitJustifyContent":"center","msFlexPack":"center","justifyContent":"center"}} onClick={onClose}><i className="material-icons" style={{"color":"white"}}>close</i></button>
			)}
		</div>
	)
}

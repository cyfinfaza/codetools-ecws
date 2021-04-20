import { React, useEffect, useRef, Children } from "react";

export default function LoadingScreen({ children, open }) {
  // var toFocus = []
  // const elementToFocus = useRef(null)
  // useEffect(() => {
  // 	if(elementToFocus.current){
  // 	console.log(elementToFocus)
  // 	elementToFocus.current.focus()}
  // }, [open])
  return (
    <div className="loadingScreen" style={open ? { opacity: 1, transform: "none", pointerEvents: "all" } : { opacity: 1, transform: "translateY(-100%)", pointerEvents: "none" }}>
      <div className="loaderContent">
        {/* <div className="loaderContent" style={{ transform: open ? "none" : "scale(1.1)" }}> */}
        {children}
      </div>
    </div>
  );
}

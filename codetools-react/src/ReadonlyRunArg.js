import React from "react";

export default function ReadonlyRunArg({ arg }) {
  const { text, output, match } = arg;
  var color = null;
  if (match != null) {
    color = match ? "#0F0" : "#FD0";
  }
  return (
    <div className="arg_readonly arg">
      <div className="inputdiv">
        <p>
          ( <span className="argText">{text}</span> )
        </p>
      </div>
      <p className="resultText monofont">
        <i className="material-icons outputArrow" style={{ width: 24, transform: "translateY(25%)", color: true && color }}>
          arrow_forwards
        </i>
        <span className="resultOutput">{output}</span>
      </p>
    </div>
  );
}

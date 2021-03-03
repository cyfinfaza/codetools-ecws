import React from "react";

export default function RunArg({ arg, onDelete, onChange}) {
  const { text, output, id } = arg;
  return (
    <div className="arg_mutable arg">
      <div className="inputdiv">
        <p>(</p>
        <input type="text" className="argin monofont" value={text} onChange={(e)=>onChange(e, id)} placeholder="args" size="1" />
        <p>)</p>
        <button className="removeButton hoverfancy" onClick={() => onDelete(id)}>
          <i className="material-icons">close</i>
        </button>
      </div>
      <p className="resultText monofont">
        <i className="material-icons outputArrow" style={{ width: 24, transform: "translateY(25%)" }}>
          arrow_forwards
        </i>
        <span className="resultOutput">{output}</span>
      </p>
    </div>
  );
}

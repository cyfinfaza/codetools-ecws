import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

if (document.getElementById("header")) document.getElementById("header").style.display = "none";

console.log(window.location.pathname);
// let editorType = window.editorType_server == "{{editorType}}" ? "editor_challenge" : window.editorType_server;
// let contentID = window.myContentID_server == "{{myContentID}}" ? "7181559b-0de6-4b78-b40d-3b719fbe8fb7" : window.myContentID_server;
let editorType = window.editorType_server == "{{editorType}}" ? "challenge" : window.editorType_server;
let contentID = window.myContentID_server == "{{myContentID}}" ? "d133b71b-3eff-4a48-90f6-040483c01b36" : window.myContentID_server;

ReactDOM.render(
  <React.StrictMode>
    <App editorType={editorType} contentID={contentID} />
  </React.StrictMode>,
  document.getElementById("root")
);

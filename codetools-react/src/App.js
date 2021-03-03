import { useRef, useEffect, useState } from "react";
import "./editorstyle.css";
import Modal from "./Modal";
import CodeFileButton from "./CodeFileButton";
import Editor from "@monaco-editor/react";
import RunArg from "./RunArg";

console.log("the app file");

let uploadInstanceCount = 1;
let globalUploadFlag = false;
let codeOnServer;
let metadataOnServer;
let argsOnServer;
let uploadBody;
const keyLang = {
  code: "java",
  starterCode: "java",
  description: "html",
};

function App({ editorType, contentID }) {
  const [metadata, setMetadata] = useState({
    title: null,
    timeout: null,
  });
  const [uploadFlag, setUploadFlag] = useState(false);
  // const [openModal, setOpenModal] = useState(null);
  const [openModal, setOpenModal] = useState("contentLoading");
  const [openCodeKey, setOpenCodeKey] = useState(null);
  const [currentCodeText, setCurrentCodeText] = useState(null);
  const [code, setCode] = useState({
    code: null,
    starterCode: null,
    description: null,
  });
  const [args, setArgs] = useState([]);
  let codeForEditor = code[openCodeKey];
  useEffect(async function () {
    fetch("/contentget?id=" + contentID)
      .then((response) => response.json())
      .then(async function (data) {
        console.log(data);
        if (data.status == "error") {
          setOpenModal("fatalError");
          console.error(data);
          return;
        }
        data = data.data;
        var metadataToSet = {};
        var codeToSet = {};
        codeToSet.code = data.code;
        setArgs(
          data.args_mutable.map((server_arg) => {
            return { id: server_arg.id, text: server_arg.arg, output: "No Output" };
          })
        );
        if (editorType == "editor_standalone" || editorType == "challenge") {
          metadataToSet.title = data.title;
          codeToSet.description = data.description;
        }
        if (editorType == "challenge") {
          codeToSet.starterCode = data.starterCode;
        }
        if (data.timeout) metadataToSet.timeout = data.timeout;
        if (editorType == "editor_challenge") {
          await fetch("/contentget?id=" + contentID)
            .then((response) => response.json())
            .then((data) => {
              metadataToSet.title = data.title;
              codeToSet.description = data.description;
            });
        }
        setCode(codeToSet);
        codeOnServer = { ...codeToSet };
        setMetadata(metadataToSet);
        metadataOnServer = { ...metadataToSet };
        setInterval(checkAndSave, 5000);
        setOpenModal(null);
        setOpenCodeKey("code");
      });
    // .catch(()=>{
    //   setOpenModal('fatalError')
    // })
  }, []);
  useEffect(() => {
    let args_mutable = args.map((arg) => {
      return { id: arg.id, arg: arg.text };
    });
    let toSend = { contentID: contentID, ...code, ...metadata, args_mutable: args_mutable };
    for (var propName in toSend) if (toSend[propName] === null || toSend[propName] === undefined) delete toSend[propName];
    uploadBody = toSend;
    setUploadFlag(true);
  }, [code, metadata, args]);
  useEffect(() => {
    globalUploadFlag = uploadFlag;
  }, [uploadFlag]);
  function checkAndSave() {
    console.log(globalUploadFlag);
    if (uploadInstanceCount == 1 && globalUploadFlag) {
      uploadInstanceCount += 1;
      setUploadFlag(false);
      fetch("/contentset", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(uploadBody) })
        .then((response) => response.json())
        .then((data) => {
          console.log(data);
          uploadInstanceCount = 1;
          // console.log("needs to be saved");
        });
    }
  }
  function handleEditorChange(e) {
    var oldCode = { ...code };
    oldCode[openCodeKey] = e;
    setCode(oldCode);
  }
  function deleteArg(argID) {
    let oldArgs = args.filter(function (item) {
      return item.id !== argID;
    });
    setArgs(oldArgs);
  }
  function changeArg(e, id) {
    let argsWillBe = args.map((arg) => {
      if (arg.id == id) arg.text = e.target.value;
      return arg;
    });
    setArgs(argsWillBe);
  }
  function newArg() {
    let oldArgs = [...args];
    oldArgs.push({ id: makeid(10), output: "No Output", text: "" });
    setArgs(oldArgs);
  }
  return (
    <>
      <div>
        <div className="modalContainer" style={openModal == null ? {} : { backgroundColor: "#8884" }}>
          <Modal open={openModal == "changeTitle"} title="Change Title" onClose={() => setOpenModal(null)}>
            <input
              onKeyDown={(event) => {
                if (event.keyCode == 13) setOpenModal(null);
              }}
              type="text"
              style={{
                width: "100%",
                boxSizing: "border-box",
                height: "32px",
              }}
              value={metadata.title ? metadata.title : ""}
              onChange={(e) => setMetadata({...metadata, title: e.target.value })}
              placeholder="New title"
            />
          </Modal>
          <Modal open={openModal == "editConfig"} title="Edit Config" onClose={() => setOpenModal(null)}>
            <div
              style={{
                display: "flex",
                flexDirection: "row",
                msFlexDirection: "row",
                flexDirection: "row",
                alignItems: "center",
                WebkitBoxAlign: "center",
                msFlexAlign: "center",
                alignItems: "center",
              }}
            >
              <label style={{ marginRight: "10px" }} htmlFor="timeout">
                Timeout:{" "}
              </label>
              {/* <input
                id="timeoutValue"
                name="timeout"
                onkeydown="if(event.keyCode == 13) {completeChangeConfiguration();}"
                type="text"
                style={{
                  width: "100%",
                  "boxSizing": "border-box",
                  height: "32px",
                }}
                placeholder="Timeout"
              /> */}
              <select value={metadata.timeout ? metadata.timeout : 5}
              onChange={(e) => setMetadata({...metadata, timeout: parseInt(e.target.value) })}>
                {(() => {
                  var output = [];
                  for (var i = 1; i <= 15; i++) {
                    output.push(
                      <option key={i} value={i}>
                        {i + " seconds"}
                      </option>
                    );
                  }
                  return output;
                })()}
              </select>
            </div>
          </Modal>
          <Modal open={openModal == "contentLoading"} title="Content Loading..." noCloseButton onClose={() => setOpenModal(null)}>
            <div className="loadingBar" style={{ width: "100%", height: 8 }}></div>
          </Modal>
          <Modal open={openModal == "fatalError"} title="Fatal Error" noCloseButton onClose={() => setOpenModal(null)}>
            <p>An error has caused this editor to stop. Check the console for details. Reoad the editor.</p>
          </Modal>
        </div>
        <div className="editor-main" style={openModal == null ? {} : { pointerEvents: "none", userSelect: "none" }}>
          <div id="descriptionSidebar" className="sidebar">
            <h1 id="contentTitle" style={{ marginBottom: "0" }}>
              {metadata.title == null ? "Loading..." : metadata.title}
            </h1>
            {editorType != "editor_challenge" && (
              <button style={{ margin: "12px", marginLeft: "0" }} onClick={() => setOpenModal("changeTitle")}>
                Change Title
              </button>
            )}
            <p style={{ marginTop: "24px" }} id="contentDescription">
              {code.description == null ? "Loading..." : code.description}
            </p>
          </div>
          <div className="threeCenter">
            {editorType == "editor_standalone" && (
              <div className="tabs">
                <CodeFileButton name="Code" keyName="code" compareKey={openCodeKey} changeKeyMethod={setOpenCodeKey} />
                <CodeFileButton name="Description" keyName="description" compareKey={openCodeKey} changeKeyMethod={setOpenCodeKey} />
              </div>
            )}
            {editorType == "challenge" && (
              <div className="tabs">
                <CodeFileButton name="Solution" keyName="code" compareKey={openCodeKey} changeKeyMethod={setOpenCodeKey} />
                <CodeFileButton name="Starter Code" keyName="starterCode" compareKey={openCodeKey} changeKeyMethod={setOpenCodeKey} />
                <CodeFileButton name="Description" keyName="description" compareKey={openCodeKey} changeKeyMethod={setOpenCodeKey} />
              </div>
            )}
            {editorType == "editor_challenge" && (
              <div className="tabs">
                <CodeFileButton name="Code" keyName="code" compareKey={openCodeKey} changeKeyMethod={setOpenCodeKey} />
              </div>
            )}
            <Editor
              id="monacoContainer"
              className="monacoContainer"
              defaultLanguage={keyLang[openCodeKey]}
              theme="vs-dark"
              options={{ minimap: { enabled: false } }}
              value={codeForEditor}
              path={openCodeKey}
              // onMount={monacoMounted}
              onChange={handleEditorChange}
            />
          </div>
          <div id="argsSidebar" className="sidebar">
            <h1>{editorType == "challenge" ? "Prepare Tests" : "Run and Test"}</h1>
            <button
              id="runbutton"
              className="fancybutton fancybutton_warn"
              style={{ width: "100%", margin: "0" }}
              // onmouseover="runButtonHovered()"
              disabled
            >
              <i className="material-icons">info</i>
              <span>Connecting to ECWS</span>
            </button>
            <div
              id="compilerError"
              style={{
                display: "none",
                flexDirection: "column",
                msFlexDirection: "column",
                flexDirection: "column",
                alignItems: "center",
                WebkitBoxAlign: "center",
                msFlexAlign: "center",
                alignItems: "center",
                color: "#F88",
              }}
            >
              <p
                style={{
                  display: "flex",
                  alignItems: "center",
                  WebkitBoxAlign: "center",
                  msFlexAlign: "center",
                  alignItems: "center",
                  marginBottom: "8px",
                }}
              >
                <i className="material-icons" style={{ marginRight: "8px" }}>
                  warning
                </i>{" "}
                Compiler Error
              </p>
              <p
                id="compilerErrorText"
                className="monofont"
                style={{
                  margin: "0",
                  fontSize: "12px",
                  msFlexItemAlign: "flex-start",
                  alignSelf: "flex-start",
                }}
              >
                Error not displayed.
              </p>
            </div>
            {editorType == "editor_challenge" && (
              <div
                id="challengeCompletedMessage"
                style={{
                  display: "none",
                  flexDirection: "column",
                  msFlexDirection: "column",
                  flexDirection: "column",
                  alignItems: "center",
                  WebkitBoxAlign: "center",
                  msFlexAlign: "center",
                  alignItems: "center",
                  color: "#8F8",
                }}
              >
                <p
                  style={{
                    display: "flex",
                    alignItems: "center",
                    WebkitBoxAlign: "center",
                    msFlexAlign: "center",
                    alignItems: "center",
                    marginBottom: "8px",
                  }}
                >
                  <i className="material-icons" style={{ marginRight: "8px" }}>
                    check_circle
                  </i>{" "}
                  Challenge Completed
                </p>
              </div>
            )}
            <div id="argslist" style={{ minHeight: "24px" }}>
              {args.map((arg) => (
                <RunArg key={arg.id} arg={arg} onChange={changeArg} onDelete={deleteArg} />
              ))}
            </div>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                msFlexDirection: "column",
                flexDirection: "column",
                alignItems: "center",
                WebkitBoxAlign: "center",
                msFlexAlign: "center",
                alignItems: "center",
                width: "100%",
              }}
            >
              <button className="hoverfancy" onClick={newArg} style={{ paddingRight: "12px", marginTop: "12px" }}>
                <i className="material-icons">add</i> New Test
              </button>
              {editorType != "editor_challenge" && (
                <button
                  id="setConfiguration"
                  className="hoverfancy"
                  onClick={() => setOpenModal("editConfig")}
                  style={{ paddingRight: "10px", marginTop: "12px" }}
                >
                  <i className="material-icons" style={{ marginRight: "4px", fontSize: "24px" }}>
                    tune
                  </i>
                  Config
                </button>
              )}
            </div>
          </div>
        </div>
        <div id="uploadStatusDiv" className="uploadStatusDiv uploadStatusColored" style={{ backgroundColor: uploadFlag ? "#FD0" : "#0F0" }}>
          <i id="uploadStatusIcon" className="material-icons" style={{ marginRight: "4px" }}>
            {uploadFlag ? "sync" : "cloud_done"}
          </i>
          <span id="uploadStatusText">{uploadFlag ? "Saving..." : "Saved"}</span>
        </div>
        <div className="uploadStatusLine uploadStatusColored" style={{ backgroundColor: uploadFlag ? "#FD0" : "#0F0" }}>
          something
        </div>
      </div>
    </>
  );
}

function makeid(length) {
  var result = "";
  var characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  var charactersLength = characters.length;
  for (var i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

export default App;

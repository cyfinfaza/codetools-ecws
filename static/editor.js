const editorSettings = {
    code: {
        language: 'java'
    },
    description: {
        language: 'html'
    },
    starterCode: {
        language: 'java'
    }
}
var codeKeys = {};
switch (editorType) {
    case 'editor_standalone':
        codeKeys = ['code', 'description']
        break;
    case 'editor_challenge':
        codeKeys = ['code']
        break;
    case 'challenge':
        codeKeys = ['code', 'description', 'starterCode']
        break;
}
// var codeKeys = ['code', 'description']
var knowCode = {};
var editorCode = {};
codeKeys.forEach(element => {
    knowCode[element] = ""
    editorCode[element] = ""
});
var editorHas = "code";
var uploadInstanceCount = 1;
var uploadFlag = false;
document.querySelector('body').style.overflow = "hidden";
var uploadStatusIcon = document.getElementById('uploadStatusIcon')
var uploadStatusText = document.getElementById('uploadStatusText')
var contentDescriptionText = document.getElementById('contentDescription')
var runbutton = document.getElementById('runbutton');
var runbutton_text = document.querySelector('#runbutton>span');
var runbutton_icon = document.querySelector('#runbutton>i');
var args;
var knowArgs;
var loaded = false;
require.config({
    paths: {
        'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.22.3/min/vs'
    }
});
let editor;
let initialRx;
fetch('/contentget?id=' + myContentID).then(response => response.json()).then(data => require(["vs/editor/editor.main"], function() {
    console.log(data)
    if (editorType == 'editor_challenge') fetch('/contentget?id=' + data.data.assocChallenge).then(response => response.json()).then(data => {
        // User doing challenge
        console.log(data)
        contentDescriptionText.innerHTML = data.data.description
        document.getElementById('contentTitle').innerHTML = data['data']['title']
    })
    else {
        // User-owned content
        document.getElementById('contentTitle').innerHTML = data['data']['title']
        document.querySelector("#changeConfiguration #timeoutValue").value = data['data']['timeout']
    }
    codeKeys.forEach(element => {
        knowCode[element] = data.data[element]
        editorCode[element] = data.data[element]
    });
    document.querySelectorAll('.tabs div').forEach(element => {
        element.classList.remove('tab_clicked')
    });
    document.querySelector('.tabs .editor-tab_' + editorHas).classList.add('tab_clicked')
    initialRx = data.data
    const tmp_args = data.data.args_mutable
    const tmp_readonly_args = data.data.args_immutable
    args = tmp_args
    knowArgs = tmp_args
    console.log(args)
    console.log(knowArgs)
    if (editorType == 'editor_challenge') genArgs(tmp_args, tmp_readonly_args)
    else genArgs(tmp_args)
    editor = monaco.editor.create(document.getElementById('monacoContainer'), {
        value: editorCode[editorHas],
        language: editorSettings[editorHas].language,
        theme: 'vs-dark',
        minimap: {
            enabled: false
        },
        automaticLayout: true,
        wordWrap: true,
        fontFamily: "DM Mono, monospace",
        disableMonospaceOptimizations: true
    });
    setInterval(() => {
        updateArgsLocal()
        editorCode[editorHas] = editor.getValue()
            // console.log(JSON.stringify(args) != JSON.stringify(knowArgs))
        var codeBad = false;
        if (editorCode.description != contentDescriptionText.innerHTML && editorType != 'editor_challenge') contentDescriptionText.innerHTML = editorCode.description
        codeKeys.forEach(element => {
            if (editorCode[element] != knowCode[element]) codeBad = true;
        });
        if (codeBad || JSON.stringify(args) != JSON.stringify(knowArgs)) {
            uploadStatusColor("#ffdd00")
            uploadStatusText.innerHTML = "Saving..."
            uploadStatusIcon.innerHTML = "sync"
            uploadFlag = true;
        } else {
            uploadStatusColor("#00ff00")
            uploadStatusText.innerHTML = "Saved"
            uploadStatusIcon.innerHTML = "cloud_done"
        }
    }, 100);
    setInterval(() => {
        if (uploadInstanceCount == 1 && uploadFlag) {
            uploadInstanceCount += 1;
            saveSession().then(() => {
                uploadInstanceCount = 1;
            })
        }
    }, 5000);
    // document.querySelector('body').addEventListener('resize', editor.layout())
    loaded = true;
}));

function uploadStatusColor(color) {
    document.querySelectorAll('.uploadStatusColored').forEach(element => {
        element.style.backgroundColor = color
    })
}

async function saveSession() {
    var toUpload = {...editorCode
    }
    var argsToUplaod = args;
    var uploadBody = {
        contentID: myContentID,
        args_mutable: argsToUplaod,
    }
    codeKeys.forEach(element => {
        uploadBody[element] = toUpload[element]
    })
    await fetch('/contentset', {
            method: 'POST', // or 'PUT'
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(uploadBody),
        })
        .then(response => {
            response.json().then(result => console.log(result))
            knowCode = {...toUpload
            }
            knowArgs = argsToUplaod;
            uploadFlag = false;
        })
}

//vestigial
async function runcode_http() {
    runbutton.classList.add("fancybutton_half")
    if (uploadFlag) {
        runbutton.innerHTML = "Saving... "
        await saveSession()
    }
    runbutton.innerHTML = "Running... "
    fetch('/runcode?id=' + myContentID)
        .then(response => response.json())
        .then(response => {
            console.log(response);
            if (response.data.run == 'success') {
                var matches = 0;
                response['data']['outputs'].forEach(result => {
                    let argElement_resultText = document.querySelector('#arg_' + result.id + ' .resultOutput')
                    argElement_resultText.innerHTML = result.output
                    let argElement_outputArrow = document.querySelector('#arg_' + result.id + ' .outputArrow')
                    switch (result.type) {
                        case 'Success':
                            if (!result.match && editorType == 'editor_challenge') argElement_outputArrow.style.color = "#ff0"
                            else argElement_outputArrow.style.color = "#0f0"
                            if (result.match) matches++
                                break;
                        case 'RuntimeError':
                            argElement_outputArrow.style.color = "#f00"
                            break;
                        case 'TimeoutError':
                            argElement_outputArrow.style.color = "#f00"
                            argElement_resultText.innerHTML = "Timed out"
                            break;
                    }
                });
                if (editorType == "editor_challenge") {
                    if (matches == response.data.outputs.length) document.getElementById("challengeCompletedMessage").style.display = "flex";
                    else document.getElementById("challengeCompletedMessage").style.display = "none";
                }
                runbutton.innerHTML = "Tests Complete"
                document.getElementById("compilerError").style.display = "none"
                    // document.getElementById('resultOutput').innerHTML = response['result']
                runbutton.classList.add("fancybutton_on")
                runbutton.classList.remove("fancybutton_half")
            } else if (response.data.run == 'compilerError') {
                runbutton.innerHTML = "Tests did not run"
                if (editorType == "editor_challenge") {
                    if (matches == response.data.outputs.length) document.getElementById("challengeCompletedMessage").style.display = "flex";
                    else document.getElementById("challengeCompletedMessage").style.display = "none";
                }
                document.getElementById("compilerErrorText").innerHTML = response.data.error
                document.getElementById("compilerError").style.display = "flex "
                runbutton.classList.add("fancybutton_warn")
                runbutton.classList.remove("fancybutton_half")
            } else if (response.data.run == 'runtimeError') {
                response['data']['outputs'].forEach(result => {
                    let argElement_resultText = document.querySelector('#arg_' + result.id + ' .resultOutput')
                    argElement_resultText.innerHTML = result.output
                });
                runbutton.innerHTML = "Tests Complete"
                document.getElementById("compilerError").style.display = "none"
                    // document.getElementById("compilerErrorText").innerHTML = response.data.error
                    // document.getElementById("compilerError").style.display = "flex"
                runbutton.classList.add("fancybutton_warn")
                runbutton.classList.remove("fancybutton_half")
            }
            if (response.data.run != 'compilerError') args.forEach(element => {
                if (document.querySelector('#arg_' + element.id + ' input').value == "") {
                    document.querySelector('#arg_' + element.id + ' .resultOutput').innerHTML = "No Output"
                }
            })
        })
        .catch((error) => {
            console.error('Error:', error);
            runbutton.innerHTML = "Server Error"
            runbutton.classList.add("fancybutton_error")
            runbutton.classList.remove("fancybutton_half")
        });
}

function runcode() {
    run_id = initialRx['_id']
    id_sig = initialRx['id_sig']
    runWS.send(JSON.stringify({ type: "runRequest", contentID: run_id, id_sig: id_sig }))
}

let runWS = new WebSocket('wss://upstairs-direct.secure1.cy2.me/ecws/runcode')
runWS.addEventListener('open', function(event) {
    releaseRunButton()
    runButtonHovered()
})
runWS.addEventListener('close', function(event) {
    runbuttonClearState()
    holdRunButton()
    runbutton.classList.add('fancybutton_error')
    runbutton_text.innerHTML = "ECWS Offline"
    runbutton_icon.innerHTML = "warning"
})
runWS.addEventListener('message', function(event) {
    topAlert(event.data)
    console.log(event.data)
})

const ARG_TEMP = document.querySelector('#argslist .arg_temp')
const ARG_READONLY_TEMP = document.querySelector('#argslist .arg_readonly_temp')
let argslist = document.querySelector('#argslist')

function newarg() {
    var args_temp = args
    var argid = makeid(10);
    args_temp.push({
        'id': argid,
        'arg': ""
    })
    fetch('/contentset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            contentID: myContentID,
            args_mutable: args_temp
        }),
    }).then(() => {
        args = args_temp
        let newarg = ARG_TEMP.cloneNode(true).content
        newarg.querySelector('.arg').id = "arg_" + argid;
        newarg.querySelector('.removeButton').addEventListener('click', function() {
            removearg(argid)
        })
        argslist.appendChild(newarg)
    })

}

function removearg(argid) {
    var args_temp = args
    for (var i = 0; i < args_temp.length; i++) {
        if (args_temp[i].id == "arg_" + argid) {
            args_temp.splice(i, 1)
            break;
        }
    };
    fetch('/contentset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            contentID: myContentID,
            args_mutable: args_temp
        }),
    }).then(() => {
        args = args_temp
        document.getElementById("arg_" + argid).remove()
    })
}

function genArgs(toGen, toGen_readonly = null) {
    if (toGen_readonly) toGen_readonly.forEach(element => {
        let newarg = ARG_READONLY_TEMP.cloneNode(true).content
        let argid = element.id
        newarg.querySelector('.arg_readonly').id = "arg_" + argid;
        newarg.querySelector('.argText').innerHTML = element.arg
        argslist.appendChild(newarg)
    });
    toGen.forEach(element => {
        let newarg = ARG_TEMP.cloneNode(true).content
        let argid = element.id
        newarg.querySelector('.arg').id = "arg_" + argid;
        newarg.querySelector('.removeButton').addEventListener('click', function() {
            removearg(argid)
        })
        newarg.querySelector('input').value = element.arg
        argslist.appendChild(newarg)
    });
}

function updateArgsLocal() {
    var args_temp = new Array;
    document.querySelectorAll('#argslist .arg_mutable').forEach(element => {
        var id = element.id;
        var arg = document.querySelector('#' + id + ' input').value
        args_temp.push({
            id: id.substring(4),
            arg: arg
        })
    });
    args = args_temp;
}

function changeEditorTo(changeTo) {
    editor.updateOptions(editorSettings[changeTo])
    monaco.editor.setModelLanguage(editor.getModel(), editorSettings[changeTo].language)
    editor.setValue(editorCode[changeTo])
    editorHas = changeTo
    document.querySelectorAll('.tabs div').forEach(element => {
        element.classList.remove('tab_clicked')
    });
    document.querySelector('.tabs .editor-tab_' + changeTo).classList.add('tab_clicked')
}

function startChangeTitle() {
    let input = document.querySelector("#changeTitle input")
    input.value = document.getElementById('contentTitle').innerHTML;
    showModal('changeTitle')
    input.focus()
}

function startConfiguration() {
    showModal('changeConfiguration')
    input.focus()
}

function completeChangeTitle() {
    let input = document.querySelector("#changeTitle input")
    topAlert("Changing title...")
    closeModal('changeTitle')
    fetch('/contentset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                contentID: myContentID,
                title: input.value
            }),
        })
        .then(response => {
            response.json().then(data => console.log(data))
            document.getElementById('contentTitle').innerHTML = input.value
            topAlert("Title changed.")
        })
}

function completeChangeConfiguration() {
    let input = document.querySelector("#changeConfiguration #timeoutValue")
    topAlert("Changing configuration...")
    closeModal("changeConfiguration")
    fetch('/contentset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                contentID: myContentID,
                timeout: parseInt(input.value)
            }),
        })
        .then(response => {
            response.json().then(data => console.log(data))
            topAlert("Configuration changed.")
        })
}
var mainApp = document.querySelector(".editor-main")
var modalContainer = document.querySelector(".modalContainer")

function showModal(id) {
    var modal = document.getElementById(id)
    modal.style.transform = 'scale(1)'
    modal.style.pointerEvents = 'all'
    modal.style.opacity = '1'
        // modal.style.display = 'inline'
    mainApp.style.filter = 'contrast(0.5)'
    mainApp.style.pointerEvents = 'none'
}

function closeModal(id) {
    var modal = document.getElementById(id)
    modal.style.transform = 'scale(0.8)'
    modal.style.pointerEvents = 'none'
    modal.style.opacity = '0'
    mainApp.style.filter = 'none'
        // modal.style.display = 'none'
    mainApp.style.pointerEvents = 'all'
}

function makeid(length) {
    var result = '';
    var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    var charactersLength = characters.length;
    for (var i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}
window.onbeforeunload = function() {
    if (uploadFlag) return ""
}
let runButtonHold = true;

holdRunButton()

function holdRunButton() {
    runButtonHold = true;
    runbutton.classList.remove("hoverfancy", "fancybutton_enabled")
    runbutton.disabled = true;
}

function releaseRunButton() {
    runButtonHold = false;
    runbutton.classList.add("fancybutton_enabled")
    runbutton.disabled = false;
}

function runbuttonClearState() {
    runbutton.classList.remove('fancybutton_on', 'fancybutton_error', 'fancybutton_warn');
}

function runButtonHovered() {
    if (!runButtonHold) {
        runbutton_text.innerHTML = "Run Code"
        runbutton_icon.innerHTML = "play_arrow"
        runbutton.classList.remove('fancybutton_on', 'fancybutton_error', 'fancybutton_warn');
    }
}
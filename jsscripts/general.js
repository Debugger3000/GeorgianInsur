


const PORT = 8000;

// State management

// Baseline states
let is_baseline = false; // does a baseline currently exist
let baseline_name = "";
let baseline_row_count = 0;
let baseline_created_at = "";
let baseline_updated_at = "";

// whether baseline is in RENAME mode
let is_rename_baseline_cur = false;

// Templates data
let insurance_templates = [];
let accounting_templates = [];



// is a process currently running and we are awaiting a response
let is_process_running = false;

// Tabs
let cur_tab = "main";

// General settings
let fall_fees_target = "---";
let winter_fees_target = "---";
let summer_fees_target = "---";


// Error message
let error_message = "";


//-------
// Application start
//-------

// run code on DOM load
document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM is fully loaded!");

    // get baseline data
    baselineData = async () => {
        await getBaseline();
    }
    baselineData();

    // template data
    templateData = async () => {
        await getTemplates();
    }
    templateData();

    
    
});



// -------------------------
// 
// Baseline functions

async function getBaseline() {
    try {
        const response = await fetch(`http://localhost:${PORT}/get-baseline`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        console.log(response);
        const data = await response.json();

        console.log("get baseline file data response:", data);

        // update baseline data...
        is_baseline = true;
        
        // update baseline row count tag and row_count variable
        updateBaselineRowCount(data.baseline_row_count);
        // update baseline name and baseline_name variable
        updateBaselineName(data.baseline_name);

    } catch (err) {
        console.error("get baseline error:", err);
    }
}


// upload new baseline report
async function uploadBaseline() {

    const fileInput = document.getElementById("baselineInput");
    const file = fileInput.files[0];

    // if (!file) {
    //     alert("Please select a file first!");
    //     return;
    // }

    console.log("sending excel file to server...");

    const formData = new FormData();
    formData.append("baseline_file", file);

    try {
        const response = await fetch(`http://localhost:${PORT}/upload-baseline`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        console.log(response);
        const data = await response.json();

        console.log("upload-baseline response returned.");
        console.log("upload baseline Server response:", data);

        if(data.status) {
            // update baseline data...
            is_baseline = true;

            // update baseline row count tag and row_count variable
            updateBaselineRowCount(data.baseline_row_count);
            // update baseline name and baseline_name variable
            updateBaselineName(data.baseline_name);
        }
        else{
            console.log("Bad baseline upload...");

            // handle error message here...

        }

        

    } catch (err) {
        console.error("upload baseline error:", err);
    }
}

function updateBaselineRowCount(row_count) {
    console.log("row count given: ", row_count);
    baseline_row_count = row_count;
    const row_tag = document.getElementById('baseline-row-count');
    row_tag.textContent = row_count;
}

function updateBaselineName(name) {
    console.log("baseline name changed to: ", name);
    baseline_name = name;
    const baseline_name_tag = document.getElementById('baselineFileName');
    baseline_name_tag.textContent = name;
}

// download baseline .xlxs or .xls
function downloadBaseline() {

    fetch(`http://localhost:${PORT}/download-baseline`)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = "report.xlsx";
            document.body.appendChild(a);
            a.click();

            window.URL.revokeObjectURL(url);
        })
        .catch(err => console.error("Download error:", err));

}


//
// ----------------------------




// script.js
async function runCompareProcess() {

    console.log("Full process function hit, baseline is: ", is_baseline);
    // 1. Baseline already exists, so we don't need to send baseline to backend


    // check if baseline file exists... this should be updated on each app load...
    if (!is_baseline) {
        alert("You need to upload a baseline file first, before you perform a full process.");
        return;
    }

    // ^^^^^
    // maybe gray out process buttons, depending on if files are available or not... QoL later.....

    // const fileInput = document.getElementById("baselineInput");
    // const file = fileInput.files[0];

    // get compare input file
    const compare_input_file = document.getElementById("compareInput");
    const compare_file = compare_input_file.files[0];


    if (!compare_file) {
        alert("Please add a compare file first before trying to do a full process !");
        return;
    }

    console.log("sending COMPARE file to server...");

    const formData = new FormData();
    formData.append("compare_file", compare_file);

    try {
        const response = await fetch(`http://localhost:${PORT}/processing/full`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        console.log(response);
        const data = await response.json();

        console.log("Full process response:", data);

        if(data.status) {
            // 
            console.log("Full process response received !");
        }
        else{
            console.log("Bad full process upload...");

            // handle error message here...

        }

        

    } catch (err) {
        console.error("Full process error:", err);
    }
}




$(document).ready(function() {
    $('#manual-add-form').on('submit', function(e) {
        e.preventDefault(); // stop normal form submission
        //e.stopPropagation();

        console.log("add studnet manmually...............");

        const form = $("#manual-add-form");

        // Serialize form to array
        const formArray = $(this).serializeArray();

        
        // Convert array to object
        const formData = {};
        $.each(formArray, function(_, field) {
            formData[field.name] = field.value;
        });

        console.log("manual student form going out...");
        

        // const form = $('#manual-add-form')[0]; // get the DOM element

        // const formData = {
        //     "Student #": form.studentNumber.value,
        //     "First Name": form.firstName.value,
        //     "Last Name": form.lastName.value,
        //     "Birthdate": form.birthdate.value,
        //     "Gender": form.gender.value,
        //     "Country of Origin": form.country.value,
        //     "Insured's Primary Email": form.email.value,
        //     "Notes": form.notes.value
        // };

        console.log(formData);

        //postStudent(formData);


        // this.reset();
        // console.log(this)
        // const form = this;
        // form[0].reset();

        // Send to Flask via fetch


        // try {
        // const res = await fetch(`http://127.0.0.1:${PORT}/add-student`, {
        //     method: "POST",
        //     headers: { "Content-Type": "application/json" },
        //     body: JSON.stringify(formData)
        // });

        // const data = await res.json();
        // console.log(data);
        // // optionally reset form: form.reset();

        // if(data){
        //     updateBaselineRowCount(data.row_count);
        //     manualFormNotif(true);
        // }

        // } catch(err) {
        //     manualFormNotif(false);
        //     console.error(err)
        // }



        fetch(`http://127.0.0.1:${PORT}/add-student`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        })
        .then(res => res.json()) // parse json response
        .then(data => {
            form[0].reset();
            
            // good response
            // display a student added to .xlxs file popup !
            console.log(data)

            if(data) {
                // update new row count
                updateBaselineRowCount(data.row_count);
                manualFormNotif(true);
            }
        })
        .catch(err => {
            manualFormNotif(false);
            console.error(err)
        });
    });
});

function testStudent() {

    const form = $('#manual-add-form')[0]; // get the DOM element

        const formData = {
            "Student #": form.studentNumber.value,
            "First Name": form.firstName.value,
            "Last Name": form.lastName.value,
            "Birthdate": form.birthdate.value,
            "Gender": form.gender.value,
            "Country of Origin": form.country.value,
            "Insured's Primary Email": form.email.value,
            "Notes": form.notes.value
        };

        // const formData = {
        //     "Student #": "TESTER",
        //     "First Name": "",
        //     "Last Name": "",
        //     "Birthdate": "",
        //     "Gender": "",
        //     "Country of Origin": "",
        //     "Insured's Primary Email": "",
        //     "Notes": ""
        // };

        console.log(formData);
    
        fetch(`http://127.0.0.1:${PORT}/add-student`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        })
        .then(res => res.json()) // parse json response
        .then(data => {
            // form[0].reset();
            
            // good response
            // display a student added to .xlxs file popup !
            console.log(data)

            if(data) {
                // update new row count
                updateBaselineRowCount(data.row_count);
                manualFormNotif(true);
            }
        })
        .catch(err => {
            manualFormNotif(false);
            console.error(err)
        });
}


// function postStudent(body) {
//     fetch(`http://127.0.0.1:${PORT}/add-student`, {
//             method: "POST",
//             headers: { "Content-Type": "application/json" },
//             body: JSON.stringify(body)
//         })
//         .then(res => res.json()) // parse json response
//         .then(data => {
//             // form[0].reset();
            
//             // good response
//             // display a student added to .xlxs file popup !
//             console.log(data)

//             if(data) {
//                 // update new row count
//                 //updateBaselineRowCount(data.row_count);
//                 //manualFormNotif(true);
//             }
//         })
//         .catch(err => {
//             manualFormNotif(false);
//             console.error(err)
//         });
// }

// takes boolean
function manualFormNotif(val) {
    const icon = document.getElementById('student-add-icon');
    
    // good response. Student added !
    if(val){
        icon.classList.remove(['svg-red','slash-circle','hidden-c'])
        // svg-green
        // check2
        icon.classList.add(['svg-green','check2'])
    }
    // bad response. Student not added
    else{
        icon.classList.remove(['svg-green','check2','hidden-c'])
        // svg-red
        // slash-circle
        icon.classList.add(['svg-red','slash-circle'])

    }
}

// -------------------------------------------



// Settings page


// add insurance template file input
const insuranceFileInput = document.getElementById("add-insurance-template-input");
const upload_insurance_button = document.getElementById("add-insurance-template");
// const compare_filename = document.getElementById("compareFileName");

upload_insurance_button.addEventListener("click", () => {
    insuranceFileInput.click(); // triggers the hidden file input
});

insuranceFileInput.addEventListener("change", async () => {
    if (insuranceFileInput.files.length > 0) {
        //compare_filename.textContent = compareFileInput.files[0].name;
        // update baseline data in server...
        await addInsuranceTemplate();
        console.log("insurance file input triggered.....");
    } else {
        //compare_filename.textContent = "No compare file selected";
    }
});


// add templates for either can just use an invisible input field...
// if file is a .xlsx or .xls then we make call to server instantly... 
// response, will trigger a call to grab all templates again showing new one added...

async function addInsuranceTemplate() {
    // add-insur-template
    console.log("about to send insurance template post");
    
    // input for add insurance temp
    // id: add-insur-template-input

    const insuranceInput = document.getElementById("add-insurance-template-input");
    const file = insuranceInput.files[0];
    

    console.log("sending excel insurance template file to server...");

    const formData = new FormData();
    formData.append("insurance_template_file", file);

    try {
        const response = await fetch(`http://localhost:${PORT}/upload-insurance-template`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        console.log(response);
        const data = await response.json();
        
        if(data.status) {
            // grab templates again
            await getTemplates();
        }

        console.log("upload-insurance template response returned.");
        console.log("upload insurance template Server response:", data);

        // look for success = true
        // grab template names again or just send back ALL insurance template names, in good response...


    } catch (err) {
        console.error("upload insurance template error:", err);
    }
}




// add accounting template file input
const accountingFileInput = document.getElementById("add-accounting-template-input");
const upload_accounting_button = document.getElementById("add-accounting-template");
// const compare_filename = document.getElementById("compareFileName");

upload_accounting_button.addEventListener("click", () => {
    accountingFileInput.click(); // triggers the hidden file input
});

accountingFileInput.addEventListener("change", async () => {
    if (accountingFileInput.files.length > 0) {
        //compare_filename.textContent = compareFileInput.files[0].name;
        // update baseline data in server...
        await addAccountingTemplate();
        console.log("insurance file input triggered.....");
    } else {
        //compare_filename.textContent = "No compare file selected";
    }
});


async function addAccountingTemplate() {
    const accountingInput = document.getElementById("add-accounting-template-input");
    const file = accountingInput.files[0];
    console.log("sending excel accounting template file to server...");

    const formData = new FormData();
    formData.append("accounting_template_file", file);

    try {
        const response = await fetch(`http://localhost:${PORT}/upload-accounting-template`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        //console.log(response);
        const data = await response.json();

        if(data.status) {
            // grab templates again
            await getTemplates();
        }

        //console.log("upload-accounting template response returned.");
        console.log("upload accounting template Server response:", data);

        // look for success = true
        // grab template names again or just send back ALL insurance template names, in good response...
    } catch (err) {
        console.error("upload accounting template error:", err);
    }
}

function confirmGeneralSettingsChanges() {
    // button id: confirm-general-settings-button

    // class when button can be clicked: rev-button-01
}


async function getTemplates() {
    try {
        const response = await fetch(`http://localhost:${PORT}/get-templates`, {
            method: "GET"
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        //console.log(response);
        const data = await response.json();

        console.log("GET templates data:", data);

        if(data.status) {
            // "accounting_templates": accounting,
            // "insurance_templates": insurance
            insurance = data.insurance_templates;
            account = data.accounting_templates;
            if(insurance && account){
                setTemplatesData(insurance, account);
                // populate insurance templates
                populateTemplateList('insurance-template-container', insurance_templates, 'insurance');
                populateTemplateList('accounting-template-container', accounting_templates, 'accounting');
            }
        }
        else{
            console.log("Bad response from Get templates req");
        }

        // look for success = true
        // grab template names again or just send back ALL insurance template names, in good response...


    } catch (err) {
        console.error("upload insurance template error:", err);
    }
}

function setTemplatesData(insurance_templates_data, accounting_templates_data) {
    insurance_templates = insurance_templates_data;
    accounting_templates = accounting_templates_data;
}

function populateTemplateList(containerId, templates, type) {

    const container = document.getElementById(containerId);
    container.innerHTML = "";

    
    if(templates.length > 0){

        templates.forEach(name => {

            const item = document.createElement('div');
            item.style.display = "flex";
            item.style.justifyContent = "space-between";
            item.style.alignItems = "center";
            item.style.padding = "1rem";
            item.style.borderRadius = "4px";
            item.style.marginBottom = "4px";
            item.style.background = "#f5f5f5ff";

            const label = document.createElement('span');
            label.textContent = name;

            const btn = document.createElement('button');
            btn.classList.add("rev-delete-button");
            btn.textContent = "Delete";

            btn.addEventListener("click", () => {
                console.log("Delete clicked for:", name, type);
                deleteTemplate(name, type);
            });

            item.appendChild(label);
            item.appendChild(btn);
            container.appendChild(item);
        });

    }
    else{
        // templates empty so just add in some filler
        const placeholder = document.createElement('h4');
        placeholder.style.padding = "1rem";
        placeholder.textContent = "No current templates.";
        container.appendChild(placeholder);
    }
    
}

async function deleteTemplate(template_name, type) {

    try {
        const response = await fetch(`http://localhost:${PORT}/templates?name=${encodeURIComponent(template_name)}&type=${encodeURIComponent(type)}`, {
            method: "DELETE"
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        //console.log(response);
        const data = await response.json();

        if(data.status) {
            // grab templates again
            await getTemplates();
            console.log("delete template successful !");
        }
        else{
            console.log("Bad response from delete templates req");
        }
    } catch (err) {
        console.error("upload insurance template error:", err);
    }
}















// 
// --------------------------------



//  BASELINE file input
// ----------------------

// Just use a custom input button, and track click / data over
// -------
const baselineFileInput = document.getElementById("baselineInput");
const uploadBtn = document.getElementById("uploadBaselineButton");
const fileName = document.getElementById("baselineFileName");

uploadBtn.addEventListener("click", () => {
    baselineFileInput.click(); // triggers the hidden file input
});

baselineFileInput.addEventListener("change", () => {
    if (baselineFileInput.files.length > 0) {
        fileName.textContent = baselineFileInput.files[0].name;
        // update baseline data in server...
        addBaseline();
    } else {
        fileName.textContent = "No file selected";
    }
});

async function addBaseline() {
    console.log("add base finc runn...");
    await uploadBaseline();
    //await getBaseline();
}


// Compare file input
// --------------------------

const compareFileInput = document.getElementById("compareInput");
const upload_compare_button = document.getElementById("uploadCompareButton");
const compare_filename = document.getElementById("compareFileName");

upload_compare_button.addEventListener("click", () => {
    compareFileInput.click(); // triggers the hidden file input
});

compareFileInput.addEventListener("change", () => {
    if (compareFileInput.files.length > 0) {
        compare_filename.textContent = compareFileInput.files[0].name;
        // update baseline data in server...
        // addBaseline();
    } else {
        compare_filename.textContent = "No compare file selected";
    }
});




function hideRenameInput() {
    const button = document.getElementById('rename-baseline-button');
    const rename_input = document.getElementById('rename-baseline-input');
    const rename_div = document.getElementById('rename-baseline-div');
    const baseline_name_span = document.getElementById('baselineFileName');
    
    // remove input field from view...
    rename_div.classList.add(['hidden-c']);
    //hide normal baseline name display
    baseline_name_span.classList.remove(['hidden-c']);
    // wipe input field empty
    rename_input.textContent = "";
    //remove red button color
    button.classList.remove(['red-button']);
    // rename button
    button.textContent = "Rename"
    console.log("set rename field to HIDE");

}

// rename baseline file
function showRenamefield() {
    // dom elements
    const button = document.getElementById('rename-baseline-button');
    const rename_input = document.getElementById('rename-baseline-input');
    const rename_div = document.getElementById('rename-baseline-div');
    const baseline_name_span = document.getElementById('baselineFileName');
    
    // currently showing rename field
    if(is_rename_baseline_cur) {
        hideRenameInput();
    }   
    else{
        // remove input field from view...
        rename_div.classList.remove(['hidden-c']);
        // make normal baeline name visible
        baseline_name_span.classList.add(['hidden-c']);
        // change button to red
        button.classList.add(['red-button']);
        // wipe input field empty
        rename_input.textContent = "";
        // rename button
        button.textContent = "Cancel"
        console.log("set rename field to SHOW");
    }
    is_rename_baseline_cur = !is_rename_baseline_cur;
}



async function submitBaselineRename() {
    console.log("subbmit baseline rename...");

    const rename_input =  document.getElementById('rename-baseline-input');
    const new_name = rename_input.value;
    console.log("new baseline name: ", new_name);

    const res = await fetch(`http://127.0.0.1:${PORT}/rename-baseline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_baseline_name: new_name })
    });

    const data = await res.json();
    console.log(data);

    if(data.status){
        //  { "new_baseline_name" : newname }
        // grab baseline data again after rename
        await getBaseline();

    }else{
        // bad req....
        // show alert of some sort...
        console.log("some sort of error in rename baseline fetch");
    }
    hideRenameInput();
}






// ---------
// Tab changing
function changeTab(type) {

    if(type === 'main' && cur_tab === 'main'){
        return;
    }
    else if(type === 'settings' && cur_tab === 'settings'){
        return;
    }

    const main = document.getElementById('main-tab');
    const main_section = document.getElementById('main-page-container');
    const settings = document.getElementById('settings-tab');
    const settings_section = document.getElementById('settings-page-wrapper');

    if(type === 'main') {
        // change cur tab variable
        cur_tab = 'main';
        // hide section'
        settings_section.classList.add(['hidden-c']);
        // unhide new tab section
        main_section.classList.remove(['hidden-c']);
        // styles
        settings.classList.remove(['active-tab']);
        main.classList.add(['active-tab']);
    }
    else{
        // change cur tab variable
        cur_tab = 'settings';
        // hide section'
        main_section.classList.add(['hidden-c']);
        // unhide new tab section
        settings_section.classList.remove(['hidden-c']);
        // styles
        main.classList.remove(['active-tab']);
        settings.classList.add(['active-tab']);
    }

}


//  Manual Add dropdown
// ----------------
// drop down for manual add
const dropdownBar = document.getElementById('manual-add-drop');
const manualForm = document.getElementById('manual-add-form');
const dropDown = document.getElementById('dropdown-icon');

// manualForm.style.display = 'none';

// dropdown clicked
// show manual form, and switch icon...
dropdownBar.addEventListener('click', () => {
    console.log("drop down for manual add ahs been clicked !");
    const containsHidden = manualForm.classList.contains('hidden-c');
    // hides
    if(!containsHidden) {
        // manualForm.style.display = 'none';
        dropDown.classList.remove(['bi-chevron-up']);
        dropDown.classList.add(['bi-chevron-down']);
        manualForm.classList.add(['hidden-c']);
    }
    // shows
    else{
        // manualForm.style.display = 'flex';
        dropDown.classList.remove(['bi-chevron-down', 'hidden-c']);
        dropDown.classList.add(['bi-chevron-up']);
        manualForm.classList.remove(['hidden-c']);
    }
})

// ---------------------------
// animations

function loadingAnimation(condition) {
    const icon = document.getElementById('process-running-icon');
    const icon_container = document.getElementById('loading-icon-container');

    // if true, we start
    if(condition) {
        // un hide loading icon
        icon_container.classList.remove(['hidden-c']);
        // add spin to the class
        icon.classList.add(['loading-animation'])

    }
    // if false we stop
    else{
        // hide loading icon
        icon_container.classList.add(['hidden-c']);
        // remove spin from class
        icon.classList.remove(['loading-animation'])
    }
}


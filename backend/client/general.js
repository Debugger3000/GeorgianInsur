


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
let esl_template = "";
let ilac_template = "";
let post_template = "";
let accounting_template = "";

// is a process currently running and we are awaiting a response
let is_process_running = false;
const tooltip_baseline = "Process a single report, and create no new baseline. This will populate multiple insurance templates and an accounting template for download from your single baseline report.";
const tooltip_against = "Process a new report against your previous baseline report. This will overwrite your current baseline file and add new students from your compare report. This will populate multiple insurance templates and an accounting report for download.";
const tooltip_settings = "Configure template excel files for main page processes to populate with data. Changing Assessment fees will adjust target value for Fees Paid columns.";

// Tabs
let cur_tab = "main";

// General settings
let fall_fees_target = "---";
let winter_fees_target = "---";
let summer_fees_target = "---";
let fall_post_fees_target = "---";
let winter_post_fees_target = "---";
let summer_post_fees_target = "---";

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

    // settings target fees
    targetFees = async () => {
        await getAccountTargets();
    }
    targetFees();

    // populated template data
    populatedTemplateData = async () => {
        await getPopTempData();
    }
    populatedTemplateData();
});



// -------------------------
// 
// Baseline functions

async function getBaseline() {
    try {
        const response = await fetch(`http://localhost:${PORT}/baseline/`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        // console.log(response);
        const data = await response.json();

        // console.log("get baseline file data response:", data);

        // update baseline data...
        is_baseline = true;
        
        // update baseline row count tag and row_count variable
        updateBaselineRowCount(data.baseline_row_count);
        // update baseline name and baseline_name variable
        updateBaselineName(data.baseline_name);
        // update last modified / updated date
        updateBaselineDate(data.updated_at);
    } catch (err) {
        console.error("get baseline error:", err);
    }
}

function updateBaselineDate(date) {
    baseline_created_at = date;
    const updated_tag = document.getElementById('baseline-updated-date');
    updated_tag.textContent = date;
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
        const response = await fetch(`http://localhost:${PORT}/baseline/`, {
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
            messageBarDisplay('success', data.message, 'main');
        }
        else{
            console.log("Bad baseline upload...");

            // handle error message here...
            messageBarDisplay('error', data.message,'main');
        }

        

    } catch (err) {
        console.error("upload baseline error:", err);
        messageBarDisplay('error', "Baseline upload failed...'",'main');
    }
}

function updateBaselineRowCount(row_count) {
    // console.log("row count given: ", row_count);
    baseline_row_count = row_count;
    const row_tag = document.getElementById('baseline-row-count');
    row_tag.textContent = row_count;
}

function updateBaselineName(name) {
    // console.log("baseline name changed to: ", name);
    baseline_name = name;
    const baseline_name_tag = document.getElementById('baselineFileName');
    baseline_name_tag.textContent = name;
}

// download baseline .xlxs or .xls
function downloadBaseline() {

    fetch(`http://localhost:${PORT}/baseline/download`, {
        method: "GET",
        cache: "no-store"
    })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            // get date
            // const cur_time = new Date();
            a.download = "baseline_report.xlsx";
            document.body.appendChild(a);
            a.click();

            window.URL.revokeObjectURL(url);
        })
        .catch(err => console.error("Download error:", err));
}


//
// ----------------------------


async function processSoloBaseline() {
    console.log("Solo process function hit, baseline is: ", is_baseline);

    // check if baseline file exists... this should be updated on each app load...
    if (!is_baseline) {
        messageBarDisplay('error', "Please upload a baseline file",'main');
        return;
    }

    // check to make sure templates exist
    // should exist 4 templates in order to process
    // EAPC, ILAC, POST, and ININ for accounting
    if(esl_template.length < 1 || ilac_template.length < 1 || post_template.length < 1 || accounting_template.length < 1 ) {
        messageBarDisplay('error', "Please upload all required templates (EAPC, ILAC, POST, ININ).",'main');
        return;
    }

    try {
        loadingAnimation(true); // start animation

        const response = await fetch(`http://localhost:${PORT}/processing/solo`, {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        console.log(response);
        const data = await response.json();
        console.log("Solo process response:", data);
        if(data.status) {
            // 
            console.log("Solo process response received !");
            messageBarDisplay('success', data.message,'main');
            //await getBaseline();
            await getPopTempData();
            await getBaseline();
        }
        else{
            console.log("Bad Solo process upload...");

            // handle error message here...
            messageBarDisplay('error', data.message,'main');
        }
        loadingAnimation(false); // stop animation

    } catch (err) {
        console.error("Full process error:", err);
        loadingAnimation(false); // stop animation
        messageBarDisplay('error', "Process Baseline failed...",'main');
    }
}



// script.js
async function runCompareProcess() {

    console.log("Full process function hit, baseline is: ", is_baseline);
    // 1. Baseline already exists, so we don't need to send baseline to backend




    // check if baseline file exists... this should be updated on each app load...
    if (!is_baseline) {
        messageBarDisplay('error', "Please upload a baseline file",'main');
        return;
    }

    // ^^^^^
    // maybe gray out process buttons, depending on if files are available or not... QoL later.....

    // const fileInput = document.getElementById("baselineInput");
    // const file = fileInput.files[0];

    // get compare input file
    const compare_input_file = document.getElementById("compareInput");
    const compare_file = compare_input_file.files[0];

    if(!compare_file) {
        messageBarDisplay('error', "Please upload a compare report first",'main');
        return;
    }

    // ask user if they are certain they want to do this action...
    const userConfirmed = await confirmActionPopUp("This process might overwrite your current baseline");
    if(!userConfirmed){
        // messageBarDisplay('success', "Please upload a compare report first");
        return;
    }

    console.log("sending COMPARE file to server...");

    const formData = new FormData();
    formData.append("compare_file", compare_file);

    try {
        loadingAnimation(true); // stop animation

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
            messageBarDisplay('success', data.message,'main');
            await getBaseline();
            await getPopTempData();
        }
        else{
            console.log("Bad full process upload...");

            // handle error message here...
            messageBarDisplay('error', data.message,'main');

        }
        loadingAnimation(false); // stop animation

    } catch (err) {
        loadingAnimation(false); // stop animation
        console.error("Full process error:", err);
        messageBarDisplay('error', "Process Against Baseline failed...",'main');
    }
}



// Add student to baseline report...
function testStudent() {

    const form = $('#manual-add-form')[0]; // get the DOM element

    // inject unique key for manually added students to notes field
    //
    let notes = "Manually Added Student:" + form.notes.value;
    console.log("Notes for manual add: ", notes);

        const formData = {
            "Student #": form.studentNumber.value,
            "First Name": form.firstName.value,
            "Last Name": form.lastName.value,
            "Birthdate": form.birthdate.value,
            "Gender": form.gender.value,
            "Country of Origin": form.country.value,
            "Insured's Primary Email": form.email.value,
            "Notes": notes
        };
        console.log(formData);
    
        fetch(`http://127.0.0.1:${PORT}/baseline/student`, {
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

            if(data.status) {
                // update new row count
                updateBaselineRowCount(data.row_count);
                // manualFormNotif(true);
                messageBarDisplay('success', data.message,'main');
                toggleStudentDrop(false);
                // reset form fields when successful
                form.studentNumber.value = "";
                form.firstName.value = "";
                form.lastName.value = "";
                form.birthdate.value = "";
                form.gender.value = "";
                form.country.value = "";
                form.email.value = "";
                form.notes.value = "";
            }
        })
        .catch(err => {
            // manualFormNotif(false);
            messageBarDisplay('success', "Add Student failed...",'main');
            console.error(err)
        });
}

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
// ---
// insurance template input setups

// add insurance template file input
const esl_input = document.getElementById("esl-insurance-input");
const esl_button = document.getElementById("esl-insurance-button");
// const compare_filename = document.getElementById("compareFileName");

esl_button.addEventListener("click", () => {
    esl_input.click(); // triggers the hidden file input
});

esl_input.addEventListener("change", async () => {
    if (esl_input.files.length > 0) {
        //compare_filename.textContent = compareFileInput.files[0].name;
        // update baseline data in server...
        await addTemplate("ESL", "esl-insurance-input");
        console.log("insurance file input triggered.....");
    } else {
        //compare_filename.textContent = "No compare file selected";
    }
});

const ilac_input = document.getElementById("ilac-insurance-input");
const ilac_button = document.getElementById("ilac-insurance-button");

ilac_button.addEventListener("click", () => {
    ilac_input.click();
});

ilac_input.addEventListener("change", async () => {
    if (ilac_input.files.length > 0) {
        await addTemplate("ILAC", "ilac-insurance-input");
        console.log("insurance file input triggered..... (ilac)");
    }
});


const post_input = document.getElementById("post-insurance-input");
const post_button = document.getElementById("post-insurance-button");

post_button.addEventListener("click", () => {
    post_input.click();
});

post_input.addEventListener("change", async () => {
    if (post_input.files.length > 0) {
        await addTemplate("POST", "post-insurance-input");
        console.log("insurance file input triggered..... (post)");
    }
});


const accounting_input = document.getElementById("accounting-insurance-input");
const accounting_button = document.getElementById("accounting-insurance-button");

accounting_button.addEventListener("click", () => {
    accounting_input.click();
});

accounting_input.addEventListener("change", async () => {
    if (accounting_input.files.length > 0) {
        await addTemplate("ACCOUNTING", "accounting-insurance-input");
        console.log("insurance file input triggered..... (inin)");
    }
});






// ------------------------------------------------

// add templates for either can just use an invisible input field...
// if file is a .xlsx or .xls then we make call to server instantly... 
// response, will trigger a call to grab all templates again showing new one added...

async function addTemplate(type, input_id) {
    // add-insur-template
    console.log("about to send insurance template post");
    
    // input for add insurance temp
    // id: add-insur-template-input

    const insuranceInput = document.getElementById(input_id);
    const file = insuranceInput.files[0];
    

    console.log("sending excel insurance template file to server...");

    const formData = new FormData();
    formData.append("template_file", file);

    try {
        const response = await fetch(`http://localhost:${PORT}/templates?type=${encodeURIComponent(type)}`, {
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
            messageBarDisplay('success', data.message,'settings');
        }

    } catch (err) {
        console.error("upload insurance template error:", err);
    }
}




// add accounting template file input
// const accountingFileInput = document.getElementById("add-accounting-template-input");
// const upload_accounting_button = document.getElementById("add-accounting-template");
// // const compare_filename = document.getElementById("compareFileName");

// upload_accounting_button.addEventListener("click", () => {
//     accountingFileInput.click(); // triggers the hidden file input
// });

// accountingFileInput.addEventListener("change", async () => {
//     if (accountingFileInput.files.length > 0) {
//         //compare_filename.textContent = compareFileInput.files[0].name;
//         // update baseline data in server...
//         await addAccountingTemplate();
//         console.log("insurance file input triggered.....");
//     } else {
//         //compare_filename.textContent = "No compare file selected";
//     }
// });


// async function addAccountingTemplate() {
//     const accountingInput = document.getElementById("add-accounting-template-input");
//     const file = accountingInput.files[0];
//     console.log("sending excel accounting template file to server...");

//     const formData = new FormData();
//     formData.append("accounting_template_file", file);

//     try {
//         const response = await fetch(`http://localhost:${PORT}/templates/accounting`, {
//             method: "POST",
//             body: formData
//         });

//         if (!response.ok) {
//             throw new Error(`Server error: ${response.status}`);
//         }
//         //console.log(response);
//         const data = await response.json();

//         if(data.status) {
//             // grab templates again
//             await getTemplates();
//             messageBarDisplay('success', data.message,'settings');
//         }

//         //console.log("upload-accounting template response returned.");
//         console.log("upload accounting template Server response:", data);

//         // look for success = true
//         // grab template names again or just send back ALL insurance template names, in good response...
//     } catch (err) {
//         console.error("upload accounting template error:", err);
//     }
// }

function confirmGeneralSettingsChanges() {
    // button id: confirm-general-settings-button

    // class when button can be clicked: rev-button-01
}


async function getTemplates() {
    try {
        const response = await fetch(`http://localhost:${PORT}/templates/`, {
            method: "GET"
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        //console.log(response);
        const data = await response.json();

        console.log(data);

        if(data.status) {
            esl_data = data.templates.esl;
            ilac_data = data.templates.ilac;
            post_data = data.templates.post;
            accounting_data = data.templates.accounting;
            
            setTemplatesData(esl_data, ilac_data, post_data, accounting_data);
            // populate insurance templates
            populateTemplateList('esl-template-container', esl_data, 'esl');
            populateTemplateList('ilac-template-container', ilac_data, 'ilac');
            populateTemplateList('post-template-container', post_data, 'post');
            populateTemplateList('accounting-template-container', accounting_data, 'accounting');

        }
        else{
            console.log("Bad response from Get templates req");
            setTemplatesData("","","","");
        }

        // look for success = true
        // grab template names again or just send back ALL insurance template names, in good response...


    } catch (err) {
        console.error("upload insurance template error:", err);
        setTemplatesData("","","","");
    }
}

function setTemplatesData(esl, ilac, post, accounting) {
    esl_template = esl;
    ilac_template = ilac;
    post_template = post;
    accounting_template = accounting;
}

function populateTemplateList(containerId, template, type) {

    const container = document.getElementById(containerId);
    container.innerHTML = "";

    console.log("template data HERE IS: ", template);
    if(template.length > 0){

        const label = document.createElement('h4');
        label.style.padding = "1rem";
        label.textContent = template;

            // const item = document.createElement('div');
            // item.style.display = "flex";
            // item.style.justifyContent = "space-between";
            // item.style.alignItems = "center";
            // item.style.padding = "1rem";
            // //item.style.borderBottom = "1px solid rgb(189, 189, 189)";
            // // item.style.maxHeight = "50px";


            // // item.style.borderRadius = "4px";
            // // item.style.marginBottom = "4px";
            // item.style.background = "#ffffff";

            // const label = document.createElement('h4');
            // label.textContent = template;

            // const btn = document.createElement('button');
            // btn.classList.add("rev-delete-button");
            // btn.textContent = "Delete";

            // btn.addEventListener("click", () => {
            //     console.log("Delete clicked for:", template, type);
            //     deleteTemplate(template, type);
            // });

            // item.appendChild(label);
            // item.appendChild(btn);
            container.appendChild(label);
    }
    else{
        // templates empty so just add in some filler
        const placeholder = document.createElement('h4');
        placeholder.style.padding = "1rem";
        placeholder.textContent = "No current template.";
        container.appendChild(placeholder);
    }
    
}

// async function deleteTemplate(template_name, type) {

//     const userConfirmed = await confirmActionPopUp("Delete this template?");

//     if (!userConfirmed) {
//         //console.log("Cancelled by user.");
//         return;
//     }

//     try {
//         const response = await fetch(`http://localhost:${PORT}/templates?name=${encodeURIComponent(template_name)}&type=${encodeURIComponent(type)}`, {
//             method: "DELETE"
//         });

//         if (!response.ok) {
//             throw new Error(`Server error: ${response.status}`);
//         }
//         //console.log(response);
//         const data = await response.json();

//         if(data.status) {
//             // grab templates again
//             await getTemplates();
//             messageBarDisplay('success', data.message,'settings');
//             console.log("delete template successful !");
//         }
//         else{
//             console.log("Bad response from delete templates req");
//             messageBarDisplay('success', data.message,'settings');
//         }
//     } catch (err) {
//         console.error("upload insurance template error:", err);
//         messageBarDisplay('success', 'Delete template failed...','settings');
//     }
// }

// populate created at date for templates at launch
async function getPopTempData(){

    try {
        const response = await fetch(`http://localhost:${PORT}/templates/metadata`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        // console.log(response);
        const data = await response.json();

        if(data.status){
            updateTemplateMetaData(data.data);
            // populate input fields with values
            // populateTargetInputs();
        }
        // console.log("get pop temp data date / rows response:", data);

    } catch (err) {
        console.error("get pop temp data error:", err);
    }

}

function updateTemplateMetaData(data) {
    const accounting = document.getElementById('ACCOUNTING-populated-created-at');
    const esl = document.getElementById('ESL-populated-created-at');
    const ilac = document.getElementById('ILAC-populated-created-at');
    const post = document.getElementById('POST-populated-created-at');

    accounting.textContent = data.ACCOUNTING.date;
    esl.textContent = data.ESL.date;
    ilac.textContent = data.ILAC.date;
    post.textContent = data.POST.date;

    // const accounting_row = document.getElementById('ACCOUNTING-row-count');
    // const esl_row = document.getElementById('ESL-row-count');
    // const ilac_row = document.getElementById('ILAC-row-count');
    // const post_row = document.getElementById('POST-row-count');

    // accounting_row.textContent = data.ACCOUNTING.row_count;
    // esl_row.textContent = data.ESL.row_count;
    // ilac_row.textContent = data.ILAC.row_count;
    // post_row.textContent = data.POST.row_count;

}














//--------
// ACCOUNTING target fees
// Get target fees

async function getAccountTargets() {

    // receive object like
    //      {
    //        "fall": 225,
    //        "winter": 225,
    //        "summer": 225
    //     }

    try {
        const response = await fetch(`http://localhost:${PORT}/settings/`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        // console.log(response);
        const data = await response.json();

        if(data.status){
            // console.log("fee targets data: ");
            updateAccountTargets(data.data);
            // populate input fields with values
            populateTargetInputs();
        }
        // console.log("get account fees data response:", data);

    } catch (err) {
        console.error("get accounting fee targets error:", err);
    }
}

function updateAccountTargets(fee_targets) {
    // post / ilac
    fall_fees_target = fee_targets.fall
    winter_fees_target = fee_targets.winter
    summer_fees_target = fee_targets.summer

    // eapc / eslg
    fall_post_fees_target = fee_targets.fall_post
    winter_post_fees_target = fee_targets.winter_post
    summer_post_fees_target = fee_targets.summer_post
}

//winter-target-fee

function populateTargetInputs() {
    //winter-target-fee
    //fall-target-fee
    //summer-target-fee

    // post / ILAC
    const fall_input = document.getElementById('fall-target-fee');
    const winter_input = document.getElementById('winter-target-fee');
    const summer_input = document.getElementById('summer-target-fee');

    // EAPC / ESLG
    const fall_input_2 = document.getElementById('fall-target-fee-02');
    const winter_input_2 = document.getElementById('winter-target-fee-02');
    const summer_input_2 = document.getElementById('summer-target-fee-02');

    fall_input.value = fall_fees_target;
    winter_input.value = winter_fees_target;
    summer_input.value = summer_fees_target;

    // EAPC / ESLG
    fall_input_2.value = fall_post_fees_target;
    winter_input_2.value = winter_post_fees_target;
    summer_input_2.value = summer_post_fees_target;

    console.log("trying to popuylate target input fields...")
}

// watching for value changes on input fields
const fall_input_watch = document.getElementById('fall-target-fee');
const winter_input_watch = document.getElementById('winter-target-fee');
const summer_input_watch = document.getElementById('summer-target-fee');

// EAPC / ESLG
const fall_input_watch_2 = document.getElementById('fall-target-fee-02');
const winter_input_watch_2 = document.getElementById('winter-target-fee-02');
const summer_input_watch_2 = document.getElementById('summer-target-fee-02');


// confirm-settings-grayed-unclickable

// Watch input fields for changes...
fall_input_watch.addEventListener("change", (e) => {
    console.log("'fall base change");
    if(e.target.value != fall_fees_target){
        general_settings_button_state(true);
        console.log("'fall value cahnged.....");
    }
})

winter_input_watch.addEventListener("change", (e) => {
    if(e.target.value != winter_fees_target){
        general_settings_button_state(true);
    }
})

summer_input_watch.addEventListener("change", (e) => {
    if(e.target.value != summer_fees_target){
        general_settings_button_state(true);
    }
})

// eapc watchers
fall_input_watch_2.addEventListener("change", (e) => {
    console.log("'fall base change");
    if(e.target.value != fall_post_fees_target){
        general_settings_button_state(true);
        console.log("'fall post value cahnged.....");
    }
})

winter_input_watch_2.addEventListener("change", (e) => {
    if(e.target.value != winter_post_fees_target){
        general_settings_button_state(true);
    }
})

summer_input_watch_2.addEventListener("change", (e) => {
    if(e.target.value != summer_post_fees_target){
        general_settings_button_state(true);
    }
})

// make confirm general settings button change state...
function general_settings_button_state(state){
    const general_settings_button = document.getElementById('confirm-general-settings-button');

    if(state){
        // remove unclickable / gray
        general_settings_button.classList.remove(['confirm-settings-grayed-unclickable'])
        // make button clickable
        general_settings_button.classList.add(['rev-button-01']);
        
    }else{
        // remove unclickable / gray
        general_settings_button.classList.remove(['rev-button-01'])
        // make button clickable
        general_settings_button.classList.add(['confirm-settings-grayed-unclickable']);
    }
}

async function postAccountFeeTargets() {
    // get input field values
    fall_val = fall_input_watch.value;
    winter_val = winter_input_watch.value;
    summer_val = summer_input_watch.value;

    fall_post_val = fall_input_watch_2.value;
    winter_post_val = winter_input_watch_2.value;
    summer_post_val = summer_input_watch_2.value;
    const form_data = {
        fall: fall_val,
        winter: winter_val,
        summer: summer_val,
        fall_post: fall_post_val,
        winter_post: winter_post_val,
        summer_post: summer_post_val,
    };
    console.log("data going to post account fees: ", form_data);

    // const formData = new FormData();
    // formData.append("baseline_file", file);

    try {
        const response = await fetch(`http://localhost:${PORT}/settings/account-fee-target`, {
            method: "POST",
            headers: {
            "Content-Type": "application/json"
        },
            body: JSON.stringify(form_data)
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        //console.log(response);
        const data = await response.json();

        if(data.status) {
            // if data post good, we grab values again...
            await getAccountTargets();
            general_settings_button_state(false); // reset button to gray once submitted and fetched new data
            messageBarDisplay('success', data.message,'settings');
        }
        else{
            messageBarDisplay('error', data.message);
        }

        //console.log("upload-accounting template response returned.");
        console.log("upload accounign target fees Server response:", data);

        // look for success = true
    } catch (err) {
        console.error("upload accounting target fees error:", err);
        messageBarDisplay('error', "Settings change failed...",'settings');
    }


}


const info_mark_div_baseline = document.getElementById('process-baseline-info-icon');
const info_mark_div_compare = document.getElementById('process-against-info-icon');
// const info_mark_div_settings = document.getElementById('settings-page-info-icon');

function createToolTip(id) {

    // Create the tooltip div
    const tooltip = document.createElement('div');
    tooltip.id = id;
    tooltip.style.position = 'absolute';
    tooltip.style.background = 'white';
    tooltip.style.padding = '12px';
    tooltip.style.borderRadius = '8px';
    tooltip.style.boxShadow = '0 8px 24px rgba(0,0,0,0.25)';
    tooltip.style.minWidth = '250px';
    tooltip.style.zIndex = '1000';
    tooltip.style.left = '50px';
    tooltip.style.top = '-50px';

    tooltip.classList.add(['border-01']);

    return tooltip;
}

info_mark_div_baseline.addEventListener('mouseover', () => {
    console.log("mouse over baseline info mark");
    const tooltip = createToolTip('info-tooltip-baseline');

    // add text
    tooltip.textContent = tooltip_baseline;
    info_mark_div_baseline.appendChild(tooltip);
});
info_mark_div_baseline.addEventListener('mouseleave', () => {
    console.log("mouse over baseline info mark LEFt LEFT LEFT");
    document.getElementById('info-tooltip-baseline').remove();
});

info_mark_div_compare.addEventListener('mouseover', () => {
    console.log("mouse over baseline info mark");
    const tooltip = createToolTip('info-tooltip-compare');

    // add text
    tooltip.textContent = tooltip_against;
    info_mark_div_compare.appendChild(tooltip);
});
info_mark_div_compare.addEventListener('mouseleave', () => {
    console.log("mouse over baseline info mark LEFt LEFT LEFT");
    document.getElementById('info-tooltip-compare').remove();
});

// settings info mark
// info_mark_div_settings.addEventListener('mouseover', () => {
//     console.log("mouse over SETTNGS ICON");
//     const tooltip = createToolTip('info-tooltip-settings');

//     // add text
//     tooltip.textContent = tooltip_settings;
//     info_mark_div_settings.appendChild(tooltip);
// });
// info_mark_div_settings.addEventListener('mouseleave', () => {
//     console.log("mouse over SETTINGS ICONSSSS LEFT");
//     document.getElementById('info-tooltip-settings').remove();
// });


// processes info marks
// append a info box to id given I think
function infoMarks(id) {
    const info_mark_div = document.getElementById(id);



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
    button.classList.remove('rev-delete-button');
    //
    button.classList.add(['rev-button-01']);
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
        //
        button.classList.remove(['rev-button-01']);

        // make normal baeline name visible
        baseline_name_span.classList.add(['hidden-c']);
        // change button to red
        button.classList.add('rev-delete-button');
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

    const res = await fetch(`http://127.0.0.1:${PORT}/baseline/rename`, {
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
        messageBarDisplay('success', data.message,'main');
    }else{
        // bad req....
        // show alert of some sort...
        console.log("some sort of error in rename baseline fetch");
        messageBarDisplay('error', data.message,'main');
    }
    hideRenameInput();
}


// ------------------------------------------------- 
function downloadFile(type) {

    fetch(`http://127.0.0.1:${PORT}/processing/download?type=${type}`, {
        method: "GET",
        cache: "no-store"
    })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            //a.download = "report.xlsx";
            document.body.appendChild(a);
            a.click();

            window.URL.revokeObjectURL(url);
        })
        .catch(err => console.error("Download error:", err));
}




// pop up window...
// call in whatever function first....
// show pop up window....
// if user clicks yes, we return true
    // user clicks no, we return false, and return out of function never executing it
function confirmActionPopUp(message) {

    const glass_overlay = document.getElementById('glass-overlay');
    const pop_up_window = document.getElementById('pop-up-window');
    const cancel_button = document.getElementById('pop-up-button-cancel');
    const confirm_button = document.getElementById('pop-up-button-confirm');

    // message
    const message_tag = document.getElementById('pop-up-message');

    return new Promise((resolve) => {

        // Update message
        message_tag.textContent = message;

        // Show popup + overlay
        glass_overlay.classList.remove(['hidden-c']);
        pop_up_window.classList.remove(['hidden-c']);
        pop_up_window.classList.add(['pop-up-window-styles']);

        const cleanup = () => {
            glass_overlay.classList.add(['hidden-c']);
            pop_up_window.classList.add(['hidden-c']);
            pop_up_window.classList.remove(['pop-up-window-styles']);
        };

        confirm_button.onclick = () => {
            cleanup();
            resolve(true);      // user confirmed
        };

        cancel_button.onclick = () => {
            cleanup();
            resolve(false);     // user canceled
        };
    });
}

// ERROR handling
// Error display bar
// show bar indefinitely... give user option to click x to close...
function messageBarDisplay(type, message, page_type) {
    console.log("message display main block ran...");
    const error_display = document.getElementById(`${page_type}-display-bar`);
    
    const message_tag = document.getElementById(`${page_type}-message`);

    error_display.classList.remove(['hidden-c']);
    message_tag.textContent = message;
    if(type === 'error') {
        // remove hidden-c, add display styles
        error_display.classList.add(['error-bar-styles']);
    }
    else{
        // success go green...
        error_display.classList.add(['success-bar-styles']);
    }
    
    
    // timeout - remove display bar after 5 seconds
    setTimeout(() => {
        console.log("message display - timeout ran...");
        if(type === 'error') {
        // remove hidden-c, add display styles
            error_display.classList.remove(['error-bar-styles']);
        }
        else{
            // success go green...
            error_display.classList.remove(['success-bar-styles']);
        }
        message_tag.textContent = "";
        error_display.classList.add(['hidden-c']);
    }, 5000)
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

function toggleStudentDrop(state) {
    // hide
    if(!state) {
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
}

// ---------------------------
// animations

function loadingAnimation(condition) {
    const icon = document.getElementById('process-running-icon');
    const icon_container = document.getElementById('loading-icon-container');

    // if true, we start
    if(condition) {
        // un hide loading icon
        icon_container.classList.remove('hidden-c');
        // add spin to the class
        icon.classList.add('loading-animation');

    }
    // if false we stop
    else{
        // hide loading icon
        icon_container.classList.add('hidden-c');
        // remove spin from class
        icon.classList.remove('loading-animation');
    }
}


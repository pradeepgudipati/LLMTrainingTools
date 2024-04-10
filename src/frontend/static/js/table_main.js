let newAnswerEditor = null;
let isCSV = false;
let uploadfileName = "";

// Toggle Edit or Save Question buttons
function toggleQuestionEditor(item_id) {
    let questionDiv = document.getElementById('question-' + item_id);
    let isEditing = questionDiv.getAttribute('contenteditable') === 'true';
    let editQuestionButton = document.getElementById('edit-q-btn-' + item_id);
    if (isEditing) {
        // Save the edited question
        let newQuestion = questionDiv.innerText;
        fetch('/update_question', {
            method: 'POST', headers: {
                'Content-Type': 'application/json',
            }, body: JSON.stringify({
                item_id: item_id, new_question: newQuestion
            }),
        })
            .then(response => response.json())
            .then(data => {
                console.log(data.message); // Handle success or error message
            })
            .catch(error => {
                console.error('Error:', error);
            });

        questionDiv.setAttribute('contenteditable', 'false');
        questionDiv.classList.remove('editing');
        editQuestionButton.querySelector('span').textContent = 'Edit Q';
        editQuestionButton.querySelector('img').src = staticUrl + "res/questionEditIcon.svg";
        questionDiv.classList.add('not-editing');
    } else {
        // Enable editing
        questionDiv.setAttribute('contenteditable', 'true');
        questionDiv.classList.add('editing');
        questionDiv.focus();
        {
            document.getElementById('edit-q-btn-' + item_id).innerText = 'Save';
        }
        editQuestionButton.querySelector('span').textContent = 'Save';
        editQuestionButton.querySelector('img').src = staticUrl + "res/saveIcon.svg";
        questionDiv.focus();
        questionDiv.classList.add('editing');
    }
}

// Toggle Answer edit or save buttons
function toggleAnswerEditor(item_id) {
    console.log('Toggling editor for item ID ' + item_id);
    let contentDiv = document.getElementById('content-' + item_id);
    let editorInstance = CKEDITOR.instances['content-' + item_id]; // Corrected instance ID
    let editAnswerButton = document.getElementById('edit-a-btn-' + item_id);
    if (contentDiv.getAttribute('contenteditable') === 'true') {
        // Switch to "Save" mode
        let data = editorInstance.getData();
        console.log("Edited html -- ", data);
        fetch('/update_answer', {
            method: 'POST', headers: {
                'Content-Type': 'application/json',
            }, body: JSON.stringify({
                item_id: item_id, content: data,
            }),
        })
            .then(response => {
                if (response.ok) {
                    // Data saved successfully, you can show a success message if needed
                    console.log('Content saved successfully');
                } else {
                    // Handle errors
                    console.error('Error saving content');
                }
            })
            .catch(error => {
                console.error('Network error:', error);
            });
        editorInstance.destroy(); // Destroy the editor instance
        contentDiv.setAttribute('contenteditable', 'false');
        contentDiv.innerHTML = data; // Update the div with the new HTML content
        editAnswerButton.querySelector('span').textContent = 'Edit A';
        editAnswerButton.querySelector('img').src = staticUrl + "res/answerEditIcon.svg";
        contentDiv.classList.add('not-editing');
    } else {
        // Switch to "Edit" mode
        console.log('Switching to edit mode');
        console.log("Editing  -- content-" + item_id);
        CKEDITOR.inline('content-' + item_id, {
            // Enable spellcheck
            scayt_autoStartup: true, // Automatically start Spell Check As You Type
            scayt_sLang: 'en_US', // Language for spellcheck (change to your desired language)
            scayt_uiTabs: '1,1,1', // Enable all SCAYT tabs (Spelling, Options, Grammar)
            contenteditable: true, // Enable contenteditable attribute on element
        }); // Corrected editor initialization
        contentDiv.setAttribute('contenteditable', 'true');

        contentDiv.focus();
        editAnswerButton.querySelector('span').textContent = 'Save';
        editAnswerButton.querySelector('img').src = staticUrl + "res/saveIcon.svg";

        // Add the 'editing' class to change the background color to white
        contentDiv.classList.add('editing');
    }
}

// Function to show the popup
function showUploadFilePopup(e) {
    console.log('---- showUploadFilePopup ----', e, e.target.id);
    document.getElementById('upload-file-popup').classList.remove('hidden');

    isCSV = e.target.id === "import-csv-link" ? true : false;
}

// Function to hide the upload file popup
function hideUploadFilePopup(e) {
    console.log('---- showUploadFilePopup ----', e, e.target.id);
    document.getElementById('upload-file-popup').classList.add('hidden');
}

// Function to show the popup
function showAddNewQAPopup() {
    document.getElementById('new-row-popup').classList.remove('hidden');
    CKEDITOR.replace('new-answer', {
        // Custom CKEditor configuration
    });
    newAnswerEditor = CKEDITOR.instances['new-answer'];
}

// Function to hide the popup
function hidePopup() {
    if (newAnswerEditor) {
        newAnswerEditor.destroy();
        newAnswerEditor = null;
    }
    document.getElementById('new-row-popup').classList.add('hidden');
}

// Existing saveNewRow function, modified to handle POST request
function saveNewRow() {
    let question = document.getElementById('new-question').value;
    let answer = newAnswerEditor.getData();

    fetch('/add', {
        method: 'POST', headers: {
            'Content-Type': 'application/json',
        }, body: JSON.stringify({
            user: question, assistant: answer
        }),
    })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            // After an add, update, or delete operation
            window.location.reload();

            // Optionally, update the table here to show the new row
            // You might need to write a function to update the DOM
        })
        .catch((error) => {
            console.error('Error:', error);
        });

    hidePopup();
}

// Function to handle Delete QA Pair
function deleteQAPair(item_id) {
    if (item_id == 1) {
        alert("Cannot delete this row");
        return;
    }

    if (item_id > 2) {
        console.log('Deleting item ID ' + item_id);
        if (confirm("Are you sure you want to delete this item?")) {
            fetch('/delete/' + item_id, {
                method: 'DELETE',
            })
                .then(response => response.json())
                .then(data => {
                    console.log('Delete Success:', data);
                    // After an add, update, or delete operation
                    window.location.reload();

                    // Optionally, remove the deleted row from the table
                    // document.getElementById('row-' + item_id).remove();
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
        }
    }
}

function handleUploadFilePopup(event) {

    if (document.getElementById('drop-zone').classList.contains("hidden")) {
        alert(" Processing the file now ")
    } else {
        uploadfileName = event.target.files[0].name;
        console.log('Selected file:', uploadfileName);
        document.getElementById('drop-zone').classList.add("hidden")
        document.getElementById('file-name').classList.remove("hidden")
        document.getElementById('upload-btn').classList.add("hidden")
        document.getElementById('process-btn').classList.remove("hidden")
        document.getElementById('file-name').textContent = uploadfileName;

    }
}

//  This function checks if the file is a CSV or JSONL file and based on that will call the appropriate function
function processUploadedFile(event) {
    let formData = new FormData();
    let fileInput = document.getElementById('dropzone-file');
    let file = fileInput.files[0];
    formData.append('file', file, uploadfileName); // append the file to the FormData object
    // if file is csv then call the function to convert csv to jsonl
    if (uploadfileName.endsWith(".csv")) {
        // Call the api to convert the csv to jsonl.
        fetch('/csv_to_jsonl', {
            method: 'POST',
            body: formData
        })
            .then(response => response.text())
            .then(data => {
                console.log('CSV to JSONL conversion response:', data);
            })
            .catch((error) => {
                console.error('Error:', error);
            });

    } else if (uploadfileName.endsWith(".jsonl")) {
        // Call the api to process the jsonl file and dump it into the database
        fetch('/import_jsonl', {
            method: 'POST',
            body: formData
        })
            .then(response => response.text())
            .then(data => {
                console.log('JSONL import response:', data);
            })
            .catch((error) => {
                console.error('Error:', error);
            });

    } else {
        alert("Please select a CSV or JSONL file")
    }
}

window.onload = function () {
// Event listener for 'Add New Row' button
    document.getElementById('add-row-btn').addEventListener('click', showAddNewQAPopup);

// Event listener for 'Upload File' button
    document.getElementById('import-jsonl-link').addEventListener('click', showUploadFilePopup);
    document.getElementById('import-csv-link').addEventListener('click', showUploadFilePopup);

// Event listener for 'Cancel' button in the upload file popup
    document.getElementById('cancel-upload-btn').addEventListener('click', hideUploadFilePopup);
    document.getElementById('upload-btn').addEventListener('click', handleUploadFilePopup);
// Event listener for 'Cancel' button in the popup
    document.getElementById('cancel-btn').addEventListener('click', hidePopup);
    document.getElementById('process-btn').addEventListener('click', processUploadedFile);

// Event listener for 'Save' button in the popup
    document.getElementById('save-btn').addEventListener('click', saveNewRow);

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            hideUploadFilePopup(event);
            hidePopup(event);
        }
    });

    document.getElementById('dropzone-file').addEventListener('change', handleUploadFilePopup);
    console.log("JS Loaded --------------------------------")
}
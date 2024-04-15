let newAnswerEditor = null;
let upload_file_name = "";

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
                showToast(data.message, false); // Handle success or error message
            })
            .catch(error => {
                showToast('Error updating question : ' + error, true); // Handle success or error message
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

function showToast(message, isError = false) {
    // Create a div element for the toast
    let toast = document.createElement('div');
    toast.className = 'toast fixed bottom-0 right-0 m-6 p-4 rounded-md transition duration-500';

    // Add classes for the appearance of the toast based on whether it's an error or not
    if (isError) {
        toast.className += ' bg-red-500 text-white';
    } else {
        toast.className += ' bg-green-500 text-white';
    }

    // Set the text of the toast to the message
    toast.textContent = message;

    // Append the toast to the body
    document.body.appendChild(toast);

    // Remove the toast after 3 seconds
    setTimeout(() => {
        toast.className += ' opacity-0';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 500);
    }, 3000);
}

// Toggle Answer edit or save buttons
function toggleAnswerEditor(item_id) {
    console.log('Toggling editor for item ID ' + item_id);
    let contentDiv = document.getElementById('content-' + item_id);
    let editorInstance = CKEDITOR.instances['content-' + item_id]; // Corrected instance ID
    let editAnswerButton = document.getElementById('edit-a-btn-' + item_id);
    if (contentDiv.getAttribute('contenteditable') === 'true') {
        // Switch to "Save" mode
        let data = editorInstance.getData("");
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
                    // console.log('Content saved successfully');
                    showToast('Content saved successfully', false); // Handle success or error message
                } else {
                    // Handle errors
                    // console.error('Error saving content');
                    showToast('Error saving content', true); // Handle success or error message
                }
            })
            .catch(error => {
                // console.error('Network error:', error);
                showToast('Network error: ' + error, true); // Handle success or error message
            });
        editorInstance.destroy(); // Destroy the editor instance
        contentDiv.setAttribute('contenteditable', 'false');
        contentDiv.innerHTML = data; // Update the div with the new HTML content
        editAnswerButton.querySelector('span').textContent = 'Edit A';
        editAnswerButton.querySelector('img').src = staticUrl + "res/answerEditIcon.svg";
        contentDiv.classList.add('not-editing');
    } else {
        // Switch to "Edit" mode
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
    document.getElementById('dropzone-file').value = "";
    document.getElementById('file-success').classList.add('hidden');
    document.getElementById('file-error').classList.add('hidden');
    document.getElementById('message-table').classList.add("hidden");
    document.getElementById('drop-zone').classList.remove("hidden")

}

// Function to hide the upload file popup
function hideUploadFilePopup(e) {
    console.log('---- showUploadFilePopup ----', e, e.target.id);
    document.getElementById('upload-file-popup').classList.add('hidden');
//     refresh the page
    window.location.reload();
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

    fetch('/add_question', {
        method: 'POST', headers: {
            'Content-Type': 'application/json',
        }, body: JSON.stringify({
            question: question, answer: answer
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
    let table_field = document.getElementById('qa-table');
    // Prevent deletion of the first row if there are only two rows
    if (item_id === 1 && table_field.rows.length <= 2) {
        showToast('Cannot delete the first row since there are only 2 rows', true); // Handle success or error message
        return;
    } else {
        console.log('Deleting item ID ' + item_id);
        if (confirm("Are you sure you want to delete this item?")) {
            fetch('/delete_question/' + item_id, {
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

// Function to handle Upload File Popup
function handleUploadFilePopup(event) {

    if (document.getElementById('drop-zone').classList.contains("hidden")) {
        showToast(" Processing the file now ")
    } else if (event.target.files && event.target.files.length > 0) {

        // Comes here when the file is selected
        upload_file_name = event.target.files[0].name;
        // Hide the dropzone and show the file name
        document.getElementById('drop-zone').classList.add("hidden")
        // Show the messages table
        document.getElementById('message-table').classList.remove("hidden");
        document.getElementById('file-name').textContent = upload_file_name;
        document.getElementById('file-success').textContent = "Click Process to import the file";
        document.getElementById('file-success').classList.remove("hidden");
        // Show the file name and hide the upload button
        document.getElementById('process-btn').classList.remove("hidden")
        document.getElementById('reset-btn').classList.remove("hidden")

    }
}

//  This function checks if the file is a CSV or JSONL file and based on that will call the appropriate function
function processUploadedFile(event) {
    let formData = new FormData();
    let fileInput = document.getElementById('dropzone-file');
    let file = fileInput.files[0];
    formData.append('file', file, upload_file_name); // append the file to the FormData object

    if (upload_file_name.endsWith(".csv")) {
        // If the file is a CSV, convert it to JSONL and then import it to the database
        fetch('/convert_csv_to_jsonl', {
            method: 'POST',
            body: formData
        })
            .then(response => response.blob())
            .then(data => {
                // The response is a Blob object containing the JSONL file
                // Create a new FormData object to send the JSONL file to the import_jsonl endpoint
                let jsonlFormData = new FormData();
                jsonlFormData.append('file', data, upload_file_name.replace('.csv', '.jsonl'));
                return fetch('/import_jsonl_to_sqlite', {
                    method: 'POST',
                    body: jsonlFormData
                });
            })
            .then(response => response.text())
            .then(data => {
                console.log('CSV to JSONL conversion and import response:', data);
                document.getElementById('file-error').textContent = "\n" + data;
                document.getElementById('file-error').classList.remove("hidden");
                if (data.toLowerCase().includes("success")) {
                    document.getElementById('process-btn').classList.add("hidden");
                    document.getElementById('reset-btn').classList.add("hidden");
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                document.getElementById('file-error').textContent = "\n" + error;
                document.getElementById('file-error').classList.remove("hidden");
            });
    } else if (upload_file_name.endsWith(".jsonl")) {
        document.getElementById('message-table').classList.remove("hidden");
        // If the file is a JSONL, directly import it to the database
        fetch('/import_jsonl_to_sqlite', {
            method: 'POST',
            body: formData
        })
            .then(response => response.text())
            .then(data => {
                console.log('JSONL import response:', data);

                document.getElementById('file-success').textContent = "\n" + data;
                document.getElementById('file-success').classList.remove("hidden");
                document.getElementById('file-error').classList.add("hidden");
                document.getElementById('file-error').textContent = "";

                if (data.toLowerCase().includes("success")) {
                    document.getElementById('process-btn').classList.add("hidden");
                    document.getElementById('reset-btn').classList.add("hidden");
                }
            })
            .catch((error) => {
                document.getElementById('file-error').textContent = "\n" + error;
                document.getElementById('file-error').classList.remove("hidden");
            });
    } else {
        alert("Please select a CSV or JSONL file")
    }
}

// Function to reset the upload file popup
function resetUploadFilePopup() {
    document.getElementById('drop-zone').classList.remove("hidden")
    document.getElementById('process-btn').classList.add("hidden")
    document.getElementById('reset-btn').classList.add("hidden")
    document.getElementById('file-name').textContent = "";
    document.getElementById('dropzone-file').value = "";
    document.getElementById('message-table').classList.add("hidden");

}

// Find Duplicates
function findDuplicates() {
    // Send a request to a new server-side route that will return only the duplicate rows
    fetch('/duplicate_checker', {
        method: 'GET',
    })
        .then(response => response.text())  // Change this line to handle HTML responses
        .then(data => {
            // The server should return the HTML for the new table, which can replace the old table
            document.body.innerHTML = data;  // Replace the entire body of the document
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}

window.onload = function () {
// Event listener for 'Add New Row' button
    document.getElementById('add-row-btn').addEventListener('click', showAddNewQAPopup);

// Event listener for 'Upload File' button
    document.getElementById('import-jsonl-link').addEventListener('click', showUploadFilePopup);
    document.getElementById('import-csv-link').addEventListener('click', showUploadFilePopup);

// Event listener for 'Cancel' button in the upload file popup
    document.getElementById('close-btn').addEventListener('click', hideUploadFilePopup);
    document.getElementById('drop-zone').addEventListener('click', handleUploadFilePopup);
// Event listener for 'Cancel' button in the popup
    document.getElementById('cancel-btn').addEventListener('click', hidePopup);
    document.getElementById('process-btn').addEventListener('click', processUploadedFile);
    document.getElementById('reset-btn').addEventListener('click', resetUploadFilePopup);

// Event listener for 'Save' button in the popup
    document.getElementById('save-btn').addEventListener('click', saveNewRow);
    document.getElementById('duplicate-check-link').addEventListener('click', findDuplicates);

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            hideUploadFilePopup(event);
            hidePopup(event);
        }
    });

    document.getElementById('dropzone-file').addEventListener('change', handleUploadFilePopup);
}
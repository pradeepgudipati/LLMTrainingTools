let newAnswerEditor = null;
let upload_file_name = "";

// Toggle Edit or Save Question buttons
function toggleQuestionEditor(item_id) {
    const questionDiv = document.getElementById('question-' + item_id);
    const isEditing = questionDiv.getAttribute('contenteditable') === 'true';
    const question_btn_text_field = document.getElementById('q-edit-button-text-' + item_id);
    const question_btn_icon_field = document.getElementById('q-edit-button-icon-' + item_id);
    if (isEditing) {
        // Save the edited question
        let newQuestion = questionDiv.innerText;
        fetch('/api/update_question', {
            method: 'POST',
            headers: {
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
        question_btn_text_field.innerText = 'Edit Q';
        question_btn_icon_field.src = staticUrl + "res/questionEditIcon.svg";
        questionDiv.classList.add('not-editing');
    } else {
        // Enable editing
        questionDiv.setAttribute('contenteditable', 'true');
        questionDiv.classList.add('editing');
        questionDiv.focus();

        question_btn_text_field.innerText = 'Save';
        question_btn_icon_field.src = staticUrl + "res/saveIcon.svg";
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
    const contentDiv = document.getElementById('content-' + item_id);
    const editorInstance = CKEDITOR.instances['content-' + item_id]; // Corrected instance ID
    const editAnswerButton = document.getElementById('edit-a-btn-' + item_id);
    if (contentDiv.getAttribute('contenteditable') === 'true') {
        // Switch to "Save" mode
        let data = editorInstance.getData("");
        fetch('/api/update_answer', {
            method: 'POST', headers: {
                'Content-Type': 'application/json',
            }, body: JSON.stringify({
                item_id: item_id, content: data,
            }),
        })
            .then(response => {
                console.log('Response:', response);
                if (response.ok) {
                    // Data saved successfully, you can show a success message if needed
                    // console.log('Content saved successfully');
                    showToast('Answer for row :: ' + item_id + ' updated successfully', false); // Handle success or error message
                } else {
                    // Handle errors
                    // console.error('Error saving content');
                    showToast('Error saving content for row :: ' + item_id, true); // Handle success or error message
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
    const question = document.getElementById('new-question').value;
    const answer = newAnswerEditor.getData("");

    fetch('/api/add_question', {
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

    } else {
        console.log('Deleting item ID ' + item_id);
        if (confirm("Are you sure you want to delete this item?")) {
            fetch('/api/delete_question/' + item_id, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
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

function downloadBlob(blob, fileName) {
    // Create a new blob object
    const newBlob = new Blob([blob]);

    // Create a link element
    const link = document.createElement('a');

    // Create an object URL for the blob
    const url = URL.createObjectURL(newBlob);

    // Set the link's href to the object URL
    link.href = url;

    // Set the download attribute of the link to the desired file name
    link.download = fileName;

    // Append the link to the body
    document.body.appendChild(link);

    // Programmatically click the link to start the download
    link.click();

    // Once the download starts, remove the link element
    document.body.removeChild(link);
}

//  This function checks if the file is a CSV or JSONL file and based on that will call the appropriate function
function processUploadedFile() {
    let formData = new FormData();
    const fileInput = document.getElementById('dropzone-file');
    const file = fileInput.files[0];
    console.log('File:', file);
    formData.append('file', file); // append the file to the FormData object
    console.log('File:', file, 'FormData -- File :', formData.get('file'));
    if (upload_file_name.endsWith(".csv")) {
        // If the file is a CSV, convert it to JSONL and then import it to the database
        fetch('/api/convert_csv_to_jsonl', {
            method: 'POST',
            body: formData
        })
            .then(response => {
                // Check if type of response is JSON or blob if json throw error
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                } else {
                    return response.blob()
                }
            })
            .then(blob => {
                console.log('CSV to JSONL conversion response:', blob);
                document.getElementById('file-error').textContent = "\n" + "File converted successfully";
                document.getElementById('file-error').classList.remove("hidden");
                // Show success message if the status is success else throw an error
                document.getElementById('process-btn').classList.add("hidden");
                document.getElementById('reset-btn').classList.add("hidden");
                // The JSONL file needs to be downloaded
                downloadBlob(blob, "training_data.jsonl")
            })
            .catch((error) => {
                console.error('Error Uploading CSV:', error);
                document.getElementById('file-error').textContent = "\n" + error.message;
                document.getElementById('file-error').classList.remove("hidden");
                showToast("Error converting file", error.message)
            });

    } else if (upload_file_name.endsWith(".jsonl")) {
        document.getElementById('message-table').classList.remove("hidden");
        // If the file is a JSONL, directly import it to the database
        fetch('/api/import_jsonl_to_sqlite', {
            method: 'POST',
            body: formData
        })
            .then(response => {
                // Check if type of response is JSON or blob if json throw error
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                } else {
                    return response.json()
                }
            })
            .then(response => {
                console.log('JSONL import response:', response);
                document.getElementById('file-success').textContent = "\n" + "JSONL data imported successfully";
                document.getElementById('file-success').classList.remove("hidden");
                document.getElementById('file-error').classList.add("hidden");
                document.getElementById('file-error').textContent = "";
                document.getElementById('process-btn').classList.add("hidden");
                document.getElementById('reset-btn').classList.add("hidden");
                showToast("JSONL File imported successfully");

            })
            .catch((error) => {
                document.getElementById('file-error').textContent = "\n" + error.message;
                document.getElementById('file-error').classList.remove("hidden");
                showToast("Error importing JSONL file")
            });
    } else {
        showToast("Please select a CSV or JSONL file");
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
    showToast("Finding duplicates - Please wait...")
    // Send a request to a new server-side route that will return only the duplicate rows
    fetch('/api/duplicate_checker', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
        .then(response => response.json())  // Change this line to handle HTML responses
        .then(data => {
            // TODO: The server should return the HTML for the new table, which can replace the old table
            console.log('Duplicate checker response:', data);
            showToast("Task Completed - " + data.message, false); // Handle success or error message
            // showToast("Duplicate File generated successfully")
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}

function showCleanTextPopup() {
    //Shows the popup
    document.getElementById('bulk-remove-text-popup').classList.remove('hidden');
    //Resets all the fields to initial state
    document.getElementById('bulk-remove-text-status').classList.add('hidden');
    document.getElementById('bulk-remove-text').value = '';
    document.getElementById('category').value = 'All Questions';
    document.getElementById('bulk-remove-text').textContent = '';
    document.getElementById('bulk-remove-text').focus();
}

function closeCleanTextPopup() {
    //hides the popup
    document.getElementById('bulk-remove-text-popup').classList.add('hidden');
}

function processCleanText() {
    // Get the text from the textarea
    const text = document.getElementById('bulk-remove-text').value;
    // Get the selection - Question or Answers category
    const category = document.getElementById('category').value;
    let isQuestion = true
    if (category.includes('answer')) {
        isQuestion = false
    }
    console.log('Category:', category);
    console.log('Text to remove:', text);
    console.log('isQuestion:', isQuestion);
    const post_body = JSON.stringify({
        'wrong_string': text,
        'isQuestion': isQuestion,
    });
    console.log("Post Body -- ", post_body);
    // Now call the clean_items_api API to remove the text
    fetch('/api/clean_items', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: post_body,
    })
        .then(response => response.json())
        .then(data => {
            console.log('Cleaned text:', data);
            // Update the textarea with the cleaned text
            document.getElementById('bulk-remove-text-status').textContent = data.message + "\n Cleaned "
                + data.total_items + ". Found text in " + data.items_with_text + " items.";
            document.getElementById('bulk-remove-text-status').classList.remove('hidden');
            //refresh the list
            window.location.reload();
        })
        .catch(error => {
            console.error('Error cleaning text:', error);
        });
}

window.onload = function () {
// Event listener for 'Add New Row' button
    document.getElementById('add-row-btn').addEventListener('click', showAddNewQAPopup);

// Event listener for 'Upload File' button
    document.getElementById('import-jsonl-link').addEventListener('click', showUploadFilePopup);
    document.getElementById('import-csv-link').addEventListener('click', showUploadFilePopup);
    // For the bulk text remover popup
    document.getElementById('bulk-remove-text-link').addEventListener('click', showCleanTextPopup);
    document.getElementById('bulk-remove-cancel-btn').addEventListener('click', closeCleanTextPopup);
    document.getElementById('bulk-remove-run-btn').addEventListener('click', processCleanText);


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
            closeCleanTextPopup();
        }
    });

    document.getElementById('dropzone-file').addEventListener('change', handleUploadFilePopup);
}
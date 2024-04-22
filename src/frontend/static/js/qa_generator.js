function generateQA() {
    // Get the input text
    const inputText = document.getElementById('text-qa-source').value;
    console.log(inputText);
    // Show the loading spinner
    document.getElementById('loading-spinner').classList.remove('hidden');
    // Send a POST request to the server
    fetch('/api/openai/qa_generator', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            'input_text': inputText,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            console.log(data);
            document.getElementById('loading-spinner').classList.add('hidden');
            // Display the result
            document.getElementById('result').textContent = data.result;
            // Update the QA pairs
            // document.getElementById('question').innerText = data['question'];
            // document.getElementById('answer').innerText = data['answer'];
        });
}

function goBackToMainScreen() {
//     Go back the main screen localhost:5000/
    window.location.href = '/';
}

window.onload = function () {
    // Add event listener for 'Generate QA' button
    document.getElementById('generate-qa-btn').addEventListener('click', generateQA);
    document.getElementById('qa-gen-cancel-btn').addEventListener('click', goBackToMainScreen);

}
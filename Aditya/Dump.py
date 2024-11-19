body {
    font-family: Arial, sans-serif;
    color: #ffffff;
    background-color: #191818;
    padding: 20px;
}

/* Headings */
h1 {
    color: #e3f9ff;
    font-size: 24px;
    margin-bottom: 10px;
}

h2 {
    color: #f5d4ff;
    font-size: 18px;
    margin-top: 20px;
}

/* Labels and input fields */
label {
    font-size: 14px;
    color: #c9c9c9;
}

input[type="file"],
input[type="textarea"],
textarea,
button {
    font-size: 16px;
    padding: 5px;
    margin: 5px 0;
    border-radius: 4px;
    border: 1px solid #3c3c3c;
    color: #ffffff;
    background-color: #0f0e0e;
}

.hidden {
    display: none;
}

#errorMessage {
    color: #ff6666;
    font-weight: bold;
    margin-top: 15px;
}

#errorMessage {
    color: #2dec46;
    font-weight: bold;
    margin-top: 15px;
    font-size: large;
}

/* Text area styling */
textarea {
    width: 95%;
    resize: none;
    background-color: #2d2d2d;
}

/* Checkbox styling */
input[type="checkbox"] {
    margin: 8px;
}

/* Button styling */
button {
    padding: 10px 15px;
    cursor: pointer;
    border: none;
    border-radius: 5px;
    font-size: 12pt;
    color: white;
    transition: background-color 0.2s ease;
}

#uploadFileBtn {
    background-color: #3b7f3d;
    color: white;
}

#uploadFileBtn:hover {
    background-color: #45a049;
    color: white;
}

#scdButton {
    background-color: #3b7f3d;
    color: white;
}

#scdButton:hover {
    background-color: #45a049;
    color: white;
}

#policyButton {
    background-color: #0b7dda;
    color: white;
}

#policyButton:hover {
    background-color: #2196f3;
}

#downloadButton {
    background-color: #3b7f3d;
}

#downloadButton:hover {
    background-color: #45a049;
}

/* Layout */
.section {
    margin-bottom: 15px;
}

/* Initially hide the uploadFile section */
.uploadFile.section {
    display: none;
}

/* Optional: Add a pointer cursor for the clickable <p> tag */
p.clickable {
    cursor: pointer;
    color: rgb(169, 169, 253);
}


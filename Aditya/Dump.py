<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SCD Policy Generator</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
  </head>

  <body>
    <h1>Cloud SCDs & Policies AI-Assist</h1>

    <!-- Text Prompt Section -->
    <div class="section">
      <h2>Enter your request</h2>
      <textarea
        rows="4"
        id="textPrompt"
        placeholder="Type your prompt here..."
      ></textarea>
    </div>

    <p class="clickable">
      Generate SCD based on Custom Organisation Policy? Upload File
    </p>

    <!-- Upload a custom dataset -->
    <div class="uploadFile section">
      <h2>Upload a file</h2>
      <div class="uploadFile">
        <form id="uploadForm">
          <input type="file" id="fileInput" />
          <p id="errorMessage" style="color: red"></p>
          <button type="submit" id="uploadFileBtn">Upload</button>
        </form>
      </div>
    </div>

    <!-- Main Buttons Section -->
    <div class="section">
      <button id="scdButton">Generate SCDs</button>
      <button id="policyButton">Generate Cloud Policy</button>
    </div>

    <br />

    <!-- Loader Section -->
    <div class="section hidden" id="loader">
      <p>Generating SCDs.. Please wait..</p>
    </div>

    <!-- Response Display Section -->
    <div class="section hidden" id="ResponseDisplay">
      <h2>SCDs Response</h2>
      <textarea
        rows="15"
        id="responseOutput"
        readonly
        placeholder="The AI response will appear here..."
      ></textarea>

      <hr />

      <!-- File Export Section -->
      <div class="section">
        <h2>Export File</h2>
        <label>Enter Export filename</label>
        <br /><br />
        <input
          type="text"
          id="filename"
          placeholder="Enter filename"
          style="
            width: 95%;
            border-radius: 5pt;
            background-color: #2d2d2d;
            color: white;
            padding: 5pt;
          "
        />

        <br /><br />

        <h3>Choose File Format:</h3>
        <input type="radio" name="fileType" value="md" /> .md <br />
        <input type="radio" name="fileType" value="csv" /> .csv <br />
        <input type="radio" name="fileType" value="xlsx" /> .xlsx <br /><br />

        <button id="downloadButton">Download File</button>
      </div>
    </div>

    <!-- Error Message Display Section -->
    <div id="errorMessage"></div>
    <div id="successMessage"></div>

    <script>
      // Show or hide loader
      function toggleLoader(show) {
        document.getElementById("loader").classList.toggle("hidden", !show);
      }

      // Show response section only after data arrives
      function showResponseSection() {
        document.getElementById("ResponseDisplay").classList.remove("hidden");
      }

      // Function to validate input fields and show error messages
      function validatePromptInput() {
        const textPrompt =
          document.getElementById("textPrompt").value.trim() !== "";
        const errorMessageDiv = document.getElementById("errorMessage");
        errorMessageDiv.innerHTML = "";
        if (!textPrompt) {
          errorMessageDiv.innerHTML = "Error: Please enter a text prompt.";
          return false;
        }
        return true;
      }

      // Send SCD Request
      document
        .getElementById("scdButton")
        .addEventListener("click", async () => {
          if (validatePromptInput()) {
            toggleLoader(true);
            const prompt = document.getElementById("textPrompt").value;

            const requestData = {
              user_prompt: prompt,
              service: "",
              additional_controls: [
                "Tagging",
                "Naming Convention",
                "Traffic Management",
              ],
              azure_controls: [
                "HTTP to HTTPS Redirection",
                "Threat Detection & Mitigation",
                "SSL/TLS Termination",
                "Application Gateway Logging",
                "Geo-Restriction",
                "Authentication and Authorization",
                "Cluster Network Security",
                "Pod Security Policies (PSPs)",
                "Node Security",
                "Auto-scaling Security",
                "Image Pull Policy",
                "Remote Desktop Protocol (RDP) Security",
                "Function Timeout and Throttling",
              ],
              benchmark_controls: [
                "Identity & Access Management",
                "Network Security",
                "Data Security & Encryption",
                "Logging and Monitoring",
                "Posture and Vulnerability Management",
                "Backup and Recovery",
              ],
            };

            try {
              const response = await fetch(
                "http://127.0.0.1:8000/generate-scd",
                {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(requestData),
                }
              );

              toggleLoader(false);

              if (response.ok) {
                const responseData = await response.json();
                document.getElementById("responseOutput").value =
                  responseData.scd || "No SCD data found in response.";
                showResponseSection();
              } else {
                const errorText = await response.text();
                document.getElementById("responseOutput").value =
                  `Error: ${response.status} - ${response.statusText}. ` +
                  `Details: ${errorText}`;
              }
            } catch (error) {
              toggleLoader(false);
              document.getElementById("responseOutput").value =
                "Request failed: " + error.message;
            }
          }
        });

      // Download File Event
      document
        .getElementById("downloadButton")
        .addEventListener("click", async () => {
          const filename = document.getElementById("filename").value.trim();
          const fileType = document.querySelector(
            "input[name='fileType']:checked"
          );
          const scdContent = document.getElementById("responseOutput").value;

          if (!filename) {
            document.getElementById("errorMessage").textContent =
              "Please enter a filename.";
            return;
          }
          if (!fileType) {
            document.getElementById("errorMessage").textContent =
              "Please select a file format.";
            return;
          }

          const requestData = {
            scd: scdContent,
            format: fileType.value,
            filename: filename,
          };

          try {
            const response = await fetch("http://127.0.0.1:8000/convert-scd", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(requestData),
            });

            if (response.ok) {
              const blob = await response.blob();
              const url = window.URL.createObjectURL(blob);
              const link = document.createElement("a");
              link.href = url;
              link.download = `${filename}.${fileType.value}`;
              link.click();
              window.URL.revokeObjectURL(url);
            } else {
              document.getElementById("errorMessage").textContent =
                "Error in file conversion.";
            }
          } catch (error) {
            document.getElementById("errorMessage").textContent =
              "Request failed: " + error.message;
          }
        });

      // Toggle Upload Section
      const paragraph = document.querySelector("p.clickable");
      const uploadSection = document.querySelector(".uploadFile.section");

      paragraph.addEventListener("click", () => {
        uploadSection.style.display = "block";
      });
    </script>
  </body>
</html>

let selectedSymptoms = [];
let allSymptoms = [];


// ================= LOAD SYMPTOMS =================

document.addEventListener("DOMContentLoaded", function () {

    loadSymptoms();

});


async function loadSymptoms() {

    try {

        const response = await fetch("http://localhost:5000/symptoms");

        const data = await response.json();

        allSymptoms = data.symptoms || [];

        const datalist = document.getElementById("symptomList");

        datalist.innerHTML = "";

        allSymptoms.forEach(symptom => {

            const option = document.createElement("option");

            option.value = symptom.replaceAll("_", " ");

            datalist.appendChild(option);

        });

    } catch (error) {

        console.error("Failed to load symptoms:", error);

    }

}


// ================= MODE TOGGLE =================

function setMode(mode) {

    document.getElementById("chatMode").style.display =
        mode === "chat" ? "block" : "none";

    document.getElementById("selectMode").style.display =
        mode === "select" ? "block" : "none";

}


// ================= CHAT MODE =================

function analyzeChat() {

    const text = document.getElementById("chatInput").value.toLowerCase();

    if (!text) {

        alert("Please describe symptoms.");

        return;

    }

    const matched = allSymptoms.filter(symptom => {

        const clean = symptom.replaceAll("_", " ");

        return text.includes(clean);

    });

    if (matched.length === 0) {

        alert("No known symptoms detected.");

        return;

    }

    sendToBackend(matched);

}


// ================= SMART SELECT MODE =================

function addSymptom() {

    const input = document.getElementById("symptomSearch");

    const value = input.value.trim().toLowerCase();

    if (value && !selectedSymptoms.includes(value)) {

        selectedSymptoms.push(value);

        renderSelected();

    }

    input.value = "";

}


function renderSelected() {

    const container = document.getElementById("selectedSymptoms");

    container.innerHTML = "";

    selectedSymptoms.forEach(symptom => {

        container.innerHTML += `

            <span class="badge bg-success me-2 mb-2">

                ${symptom}

            </span>

        `;

    });

}


function analyzeSelected() {

    if (selectedSymptoms.length === 0) {

        alert("Please add at least one symptom.");

        return;

    }

    sendToBackend(selectedSymptoms);

}


// ================= BACKEND CALL =================

async function sendToBackend(symptoms) {

    // Show loading

    document.getElementById("loading").style.display = "none";

    document.getElementById("resultCard").style.display = "block";

    const nextPanel = document.getElementById("nextActions");

    if (nextPanel) {
        nextPanel.style.display = "block";
    }
    
    try {

        // Normalize format to dataset style

        const normalized = symptoms.map(symptom =>
            symptom.toLowerCase().replaceAll(" ", "_")
        );


        const response = await fetch("http://localhost:5000/predict", {

            method: "POST",

            credentials: "include",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                symptoms: normalized

            })

        });


        // Handle unauthorized session

        if (response.status === 401) {

            window.location.href = "login.html";

            return;

        }


        const data = await response.json();


        if (!response.ok) {

            alert(data.error || "Prediction failed.");

            return;

        }


        // ================= DISPLAY RESULTS =================


        document.getElementById("diseaseName").innerText =

            data.disease;


        // Risk Badge

        const riskBadge = document.getElementById("riskBadge");

        riskBadge.innerText =

            "Risk Level: " + data.risk_level;


        if (data.risk_level === "HIGH") {

            riskBadge.className = "badge bg-danger fs-6";

        }

        else if (data.risk_level === "MODERATE") {

            riskBadge.className =

                "badge bg-warning text-dark fs-6";

        }

        else {

            riskBadge.className = "badge bg-success fs-6";

        }


        // Confidence bar

        const confidence = parseFloat(data.confidence).toFixed(2);

        const bar = document.getElementById("confidenceBar");

        bar.style.width = confidence + "%";

        bar.innerText = confidence + "%";


        // Top predictions list

        const topList = document.getElementById("topPredictions");

        topList.innerHTML = "";


        data.top_predictions.forEach(item => {

            topList.innerHTML += `

                <li>

                    ${item.disease}

                    – ${item.probability.toFixed(2)}%

                </li>

            `;

        });


        // AI Explanation

        document.getElementById("explanationText").innerText =

            data.explanation;


        // Specialist suggestion

        document.getElementById("specialistText").innerText =

            mapSpecialist(data.disease);


        // Hide loading

        document.getElementById("loading").style.display = "none";


        // Show result card

        document.getElementById("resultCard").style.display = "block";


        // Show next actions panel

        document.getElementById("nextActions").style.display = "block";


    }

    catch (error) {

        document.getElementById("loading").style.display = "none";

        alert("Error connecting to backend.");

        console.error(error);

    }

}


// ================= SPECIALIST MAPPING =================

function mapSpecialist(disease) {

    const mapping = {

        "Fungal infection": "Dermatologist",

        "Heart attack": "Cardiologist",

        "Migraine": "Neurologist",

        "Diabetes": "Endocrinologist"

    };


    return mapping[disease] ||

        "General Physician";

}
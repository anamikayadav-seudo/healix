async function analyzeHealth() {

    const data = {

        height: document.getElementById("height").value,
        weight: document.getElementById("weight").value,
        steps: document.getElementById("steps").value,
        sleep_hours: document.getElementById("sleep").value,
        water_intake: document.getElementById("water").value,
        calories_intake: document.getElementById("calories").value

    };


    // Validation

    if (!data.height || !data.weight || !data.steps ||
        !data.sleep_hours || !data.water_intake || !data.calories_intake) {

        alert("Please fill all fields.");
        return;

    }


    try {

        const response = await fetch(
            "http://localhost:5000/health-track",
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                credentials: "include",

                body: JSON.stringify(data)

            }
        );


        if (response.status === 401) {

            window.location.href = "login.html";

            return;

        }


        const result = await response.json();

        console.log(result);


        document.getElementById("healthResults").style.display = "flex";


        // ================= BMI =================

        document.getElementById("bmiResult").innerText =
            result.bmi;

        document.getElementById("bmiStatus").innerText =
            result.bmi_status;

        document.getElementById("bmiStatus").style.color =
            result.bmi_color;


        // ================= BMR =================

        document.getElementById("bmrResult").innerText =
            result.bmr;

        document.getElementById("bmrExplanation").innerText =
            result.bmr_explanation;


        // ================= HEALTH SCORE =================

        document.getElementById("scoreResult").innerText =
            result.health_score + "/100";

        document.getElementById("scoreStatus").innerText =
            result.health_status;

        document.getElementById("scoreStatus").style.color =
            result.health_color;


        // ================= GAUGE ANIMATION =================

        const gauge = document.getElementById("gaugeFill");

        if (gauge) {

            const circumference = 251;

            const progress =
                circumference - (result.health_score / 100) * circumference;

            gauge.style.strokeDashoffset = progress;


            // Dynamic gauge color

            if (result.health_score >= 80)
                gauge.style.stroke = "#00ff88";

            else if (result.health_score >= 50)
                gauge.style.stroke = "#ffaa00";

            else
                gauge.style.stroke = "#ff4444";

        }


        // ================= ALERTS =================

        if (result.alerts && result.alerts.length > 0) {

            document.getElementById("alerts").innerHTML =
                result.alerts.join("<br>");

        }

        else {

            document.getElementById("alerts").innerHTML =
                "No alerts detected ✅";

        }


        // ================= AI SUGGESTIONS =================

        document.getElementById("aiSuggestions").innerText =
            result.ai_suggestions || "Suggestions unavailable";


        // ================= AI SUMMARY =================

        document.getElementById("aiSummary").innerText =
            result.ai_summary || "Summary unavailable";


    }

    catch (error) {

        console.error(error);

        alert("Error submitting health data.");

    }

}
document.addEventListener("DOMContentLoaded", () => {

    const container = document.getElementById("historyContainer");

    if (!container) return;

    loadHistory();

});

async function loadHistory() {

    const container = document.getElementById("historyContainer");

    if (!container) return;

    try {

        const response = await fetch("http://localhost:5000/history", {
            credentials: "include"
        });

        if (response.status === 401) {
            window.location.href = "login.html";
            return;
        }

        const history = await response.json();

        if (!history.length) {
            container.innerHTML = `
                <p class="text-muted">No prediction history available.</p>
            `;
            return;
        }

        container.innerHTML = "";

        history.forEach(item => {

            container.innerHTML += `
                <div class="card glass-card mb-3 p-3">

                    <h5>${item.disease}</h5>

                    <p><strong>Symptoms:</strong> ${item.symptoms}</p>

                    <p>
                        Confidence:
                        <span class="badge bg-primary">
                            ${item.confidence.toFixed(2)}%
                        </span>
                    </p>

                    <p>
                        Risk Level:
                        <span class="badge ${
                            item.risk_level === "HIGH"
                                ? "bg-danger"
                                : item.risk_level === "MODERATE"
                                ? "bg-warning text-dark"
                                : "bg-success"
                        }">
                            ${item.risk_level}
                        </span>
                    </p>

                    <small class="text-muted">
                        ${item.date}
                    </small>

                    <br>

                    <button class="btn btn-sm btn-outline-danger mt-2"
                        onclick="deleteHistory(${item.id})">
                        Delete
                    </button>

                </div>
            `;
        });

    } catch (error) {

        console.error("History load failed:", error);

    }
}

async function deleteHistory(id) {

    if (!confirm("Delete this record?")) return;

    await fetch(`http://localhost:5000/delete-history/${id}`, {
        method: "DELETE",
        credentials: "include"
    });

    loadHistory();
}
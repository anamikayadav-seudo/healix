/* ======================================================
   LOAD HEADER + FOOTER COMPONENTS
====================================================== */

async function loadComponent(id, file) {

    const response = await fetch(file);
    const data = await response.text();

    document.getElementById(id).innerHTML = data;

    if (id === "header") {
        updateAuthUI();
    }

}

loadComponent("header", "components/header.html");
loadComponent("footer", "components/footer.html");


/* ======================================================
   AUTH UI NAVBAR CONTROL
====================================================== */

async function updateAuthUI() {

    try {

        const response = await fetch(
            "http://localhost:5000/check-session",
            {
                method: "GET",
                credentials: "include"
            }
        );

        const data = await response.json();

        console.log("Session response:", data); // DEBUG LINE

        const authArea = document.getElementById("authArea");

        if (!authArea) return;


        /* ================= USER LOGGED IN ================= */

        if (data.logged_in === true && data.username) {

            authArea.innerHTML = `
                <span class="me-2 fw-semibold">
                    Hello, ${data.username} 👋
                </span>

                <a href="history.html"
                   class="btn btn-outline-secondary btn-sm me-2">
                   History
                </a>

                <button onclick="logoutUser()"
                        class="btn btn-danger btn-sm">
                        Logout
                </button>
            `;

        }


        /* ================= USER NOT LOGGED IN ================= */

        else {

            authArea.innerHTML = `
                <a href="login.html"
                   class="btn btn-outline-secondary btn-sm me-2">
                   Login
                </a>

                <a href="register.html"
                   class="btn btn-main btn-sm">
                   Register
                </a>
            `;

        }

    }

    catch (error) {

        console.error("Session check failed:", error);

    }

}


/* ======================================================
   LOGOUT FUNCTION
====================================================== */

async function logoutUser() {

    await fetch(
        "http://localhost:5000/logout",
        {
            method: "POST",
            credentials: "include"
        }
    );

    location.reload();

}
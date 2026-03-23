let map;


async function findSpecialist() {

    const disease =
        document.getElementById("diseaseInput").value;

    const location =
        document.getElementById("locationInput").value;


    if (!disease || !location) {

        alert("Enter disease and location");

        return;

    }


    const response =
        await fetch("http://localhost:5000/find-specialist", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                disease,
                location

            })

        });


    const result = await response.json();


    const container =
        document.getElementById("specialistResults");


    container.style.display = "flex";


    container.innerHTML = `

    <div class="col-md-12">

    <div class="glass-card result-card">

    <h4>Recommended Specialist</h4>

    <h2>${result.recommended_specialist}</h2>

    </div>

    </div>

    `;


    result.hospitals.forEach(hospital => {

        container.innerHTML += `

        <div class="col-md-4">

        <div class="glass-card result-card">

        <h5>${hospital.name}</h5>

        <p>${hospital.address}</p>

        <button
        class="btn btn-main mt-2"
        onclick="openAppointmentModal()"
        >

        Book Appointment

        </button>

        </div>

        </div>

        `;

    });


    showMap(result.hospitals);

}



function showMap(hospitals) {

    if (!hospitals.length) return;


    if (map) {

        map.remove();

    }


    map = L.map("hospitalMap").setView(

        [

            hospitals[0].latitude,
            hospitals[0].longitude

        ],

        13

    );


    L.tileLayer(

        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",

        {

            attribution:
            "&copy; OpenStreetMap contributors"

        }

    ).addTo(map);


    hospitals.forEach(hospital => {

        L.marker([

            hospital.latitude,
            hospital.longitude

        ])

        .addTo(map)

        .bindPopup(

            `<b>${hospital.name}</b>`

        );

    });

}



function openAppointmentModal() {

    const modal =
        new bootstrap.Modal(
            document.getElementById("appointmentModal")
        );

    modal.show();

}



function submitAppointment() {

    alert("Appointment request submitted successfully!");

}
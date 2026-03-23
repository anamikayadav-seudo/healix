async function goToScan(){

    try{
        const response = await fetch("http://localhost:5000/history",{
            credentials:"include"
        });

        if(response.status === 401){
            window.location.href = "login.html";
        }else{
            window.location.href = "scan.html";
        }

    }catch(error){
        window.location.href = "login.html";
    }
}
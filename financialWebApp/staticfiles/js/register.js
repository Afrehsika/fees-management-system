const UsernameField = document.querySelector("#UsernameField");
const feedBackArea = document.querySelector(".invalid-feedback");
const EmailField = document.querySelector("#EmailField");
const EmailfeedBackArea = document.querySelector(".Email-feedback ");
const showPasswordToggle = document.querySelector(".showPasswordToggle");
const PasswordField = document.querySelector("#PasswordField");
const submitBtn = document.querySelector(".submitBtn");


const handleToggleInput = (e) =>{
    if (showPasswordToggle.textContent === "SHOW"){
        showPasswordToggle.textContent = "HIDE";
        PasswordField.setAttribute("type","text")
    }else{
        showPasswordToggle.textContent = "SHOW"; 
        PasswordField.setAttribute("type","password") 
    }
};

showPasswordToggle.addEventListener("click",handleToggleInput);


EmailField.addEventListener("keyup", (e) =>{
    const emailval = e.target.value;
    console.log(emailval)

    EmailField.classList.remove("is-invalid")
    EmailfeedBackArea.style.display = "none";

    if (emailval.length > 0){
        fetch("/authentication/validate-email",{
            body:JSON.stringify({email:emailval}), method:"POST",
        }).then(res=>res.json()).then(data=>{
            console.log(data)
            if(data.email_error){
                submitBtn.disabled=true
                EmailField.classList.add("is-invalid")
                EmailfeedBackArea.style.display = "block";
                EmailfeedBackArea.innerHTML = `<p>${data.email_error}</p>`
            }else{
                submitBtn.removeAttribute("disabled")
            }
        });
    };

})



UsernameField.addEventListener("keyup",(e)=>{
    const usernameVal = e.target.value;
    console.log(usernameVal)

    UsernameField.classList.remove("is-invalid")
    feedBackArea.style.display = "none";

    if (usernameVal.length > 0){
        fetch("/authentication/validate-username",{
            body:JSON.stringify({username:usernameVal}), method:"POST",
        }).then(res=>res.json()).then(data=>{
            console.log(data)
            if(data.username_error){
                UsernameField.classList.add("is-invalid")
                feedBackArea.style.display = "block";
                feedBackArea.innerHTML = `<p>${data.username_error}</p>`
                submitBtn.disabled = true
            }else{
                submitBtn.removeAttribute("disabled")
            }
        });
    };
    

});
const username = localStorage.getItem("username")
if(!username){
    const name  = prompt('Your Name ')
    localStorage.setItem("username",name)
   
}

const userdiv = document.getElementById("userdiv")
userdiv.textContent=username;
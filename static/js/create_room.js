const create_room = document.querySelector("#create_room")
const new_room = document.querySelector("#new_room")
const room_name = document.querySelector("#room_name")
const join_room = document.querySelector("#join_room")
const username = document.querySelector("#username")
var regexp = /^\S*$/;
const join_room_btn = document.querySelector("#join_room_btn")

username.value=localStorage.getItem('username')||''


join_room.addEventListener('click',function(){
    room_name.classList.remove('d-none')
    new_room.classList.add('d-none')
    join_room.classList.add('d-none')
    join_room_btn.classList.remove('d-none')
})
new_room.addEventListener('click',function(){
    room_name.classList.remove('d-none')
    new_room.classList.add('d-none')
    join_room.classList.add('d-none')
    create_room.classList.remove('d-none')
})
create_room.addEventListener('click',function(){
    if(!room_name.value.match(regexp)){
        Swal.fire("Error", "Space not Allowed", "error");
        
    }
    else{
        if(username.value.length <3){
            Swal.fire("Error", "Username must be larger than 3 letters", "error");
        }
        else{
            localStorage.setItem('username', username.value)
            window.location.href = window.location.href+room_name.value
        }
    }
    
})
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
    join_room.classList.add('d-none')
    join_room_btn.classList.remove('d-none')
})
new_room.addEventListener('click',function(){
    room_name.classList.remove('d-none')
    new_room.classList.add('d-none')
    create_room.classList.remove('d-none')
})
function getInRoom() {
    
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
        
    
}

create_room.addEventListener('click',async function(){
    try {
        const res = await fetch(`https://bingoboi.herokuapp.com/room/check_room/${room_name.value}/`,{
            method:'GET',
        
        })
        const r = await res.json()
        if(r.room_exist){
            Swal.fire("Room Name Taken", "Please choose other or join this room ! ", "error");
        }
        else{
            getInRoom()  
        }
    } catch (error) {
        console.log(error)
    }
    // getInRoom()
})
join_room_btn.addEventListener('click',getInRoom)
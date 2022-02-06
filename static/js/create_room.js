const create_room = document.querySelector("#create_room")
const room_name = document.querySelector("#room_name")
var regexp = /^\S*$/;
create_room.addEventListener('click',function(){
    if(room_name.value.match(regexp)){
        window.location.href = window.location.href+room_name.value
     
    }
    else{
        Swal.fire("Error", "Space not Allowed", "error");
    }
    
})
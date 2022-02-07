const infodiv = document.getElementById("infodiv")

const urls = "ws://127.0.0.1:8000/ws/clicked"+window.location.pathname;
const ws = new WebSocket(urls);
const addmearr = [];
const loc_username = localStorage.getItem("username")
ws.onopen = function (e) {
  console.log("connection open");
  
  ws.send(JSON.stringify({
      command:'joined',
      info:`${loc_username} just Joined `,
      user:loc_username,
  }))
};

ws.onerror = function (e) {
  console.log("error is ", e);
};
ws.onmessage = function (e) {
  const data = JSON.parse(e.data);
  const command = data.command
  console.log(data)
  if(command ==='clicked'){
    const clickedDiv = document.querySelector(
        `[data-innernum='${data.dataset}']`
      );
      addmearr.push(data.dataset)
      clickedDiv.classList.add("clicked");
  }
  if(command ==='joined'){
      if(data.user !== loc_username){
        infodiv.innerHTML+=`<p style="font-size:12px;">${data.info}</p>`
      }
   
  }

};
ws.onclose = function (e) {

  ws.send(JSON.stringify(
    {
      command:"left",
      user:loc_username,
    }
  ))
};
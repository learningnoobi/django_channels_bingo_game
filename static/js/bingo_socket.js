const infodiv = document.getElementById("infodiv");
const user_num = document.getElementById("user_num");
const userTurn = document.getElementById("userTurn");
//for developent
// const urls = "wss://127.0.0.1:8000/ws/clicked" + window.location.pathname;

const urls = "wss://bingoboi.herokuapp.com/ws/clicked" + window.location.pathname;


const ws = new ReconnectingWebSocket(urls);
const addmearr = [];
const loc_username = localStorage.getItem("username");

let allPlayers = [];
let total_player;
let playerTrack = 0;
let currPlayer;
ws.onopen = function (e) {
  ws.send(
    JSON.stringify({
      command: "joined",
      info: `${loc_username} just Joined `,
      user: loc_username,
    })
  );
};

function notForMe(data) {
  return data.user !== loc_username;
}

ws.onerror = function (e) {
  console.log("error is ", e);
};
ws.onmessage = function (e) {
  const data = JSON.parse(e.data);
  const command = data.command;
  if (command === "joined") {
    allPlayers = data.all_players;
    total_player = data.users_count;

    currPlayer = allPlayers[playerTrack];
    userTurn.textContent=currPlayer===loc_username ?"Your ":`${currPlayer}'s`


    console.log('joined now is ',currPlayer);
    user_num.textContent = data.users_count;
    if (notForMe(data)) {
      infodiv.innerHTML += `<p style="font-size:12px;">${data.info}</p>`;
    }
  }
  if (command === "clicked") {
    checkTurn()
   

    const clickedDiv = document.querySelector(
      `[data-innernum='${data.dataset}']`
    );

    if (notForMe(data)) {
      const myDataSetId = parseInt(clickedDiv.dataset.id);

      if (!addmearr.includes(myDataSetId)) {
        addmearr.push(myDataSetId);
        loopItemsAndCheck();
      }
    }
    clickedDiv.classList.add("clicked");
  }

  if (command === "won") {
    if (notForMe(data)) {
      Swal.fire("You Lost", data.info, "error");
    }
  }
};
ws.onclose = function (e) {
  console.log("closed");
};


function checkTurn() {
  if (playerTrack === total_player-1) {
    playerTrack = 0;
    currPlayer = allPlayers[playerTrack];
    userTurn.textContent=currPlayer===loc_username ?"Your ":`${currPlayer}'s`
   
  } else {
    playerTrack++;
    currPlayer = allPlayers[playerTrack];
    userTurn.textContent=currPlayer===loc_username ?"Your ":`${currPlayer}'s`
  }
}
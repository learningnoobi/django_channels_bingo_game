const infodiv = document.getElementById("infodiv");
const user_num = document.getElementById("user_num");
const userTurn = document.getElementById("userTurn");
const sidebar = document.getElementById("sidebar");
const chatInput = document.getElementById("chat-input");
let lastStep = 0;
// Connect back to whichever host served this page (ws:// locally, wss:// over HTTPS).
const wsScheme = window.location.protocol === "https:" ? "wss://" : "ws://";
const urls = wsScheme + window.location.host + "/ws/clicked" + window.location.pathname;
let gamestate = "ON";
const ws = new ReconnectingWebSocket(urls);
const addmearr = [];
const loc_username = localStorage.getItem("username");

let allPlayers = [];
let total_player;
let playerTrack = 0;
let currPlayer;

window.onbeforeunload = function (event) {
 if(gamestate !== "ON") return;
  return "Do you really want to refresh?"
};

// Everything that arrives over the socket (user names, chat, info) is untrusted: escape it
// before putting it into HTML.
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[ch]);
}

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

ws.onmessage = function (e) {
  const data = JSON.parse(e.data);
  const command = data.command;

  if (command === "joined") {
    allPlayers = data.all_players;
    total_player = data.users_count;
    currPlayer = allPlayers[playerTrack];
    userTurn.textContent =
      currPlayer === loc_username ? "Your " : `${currPlayer}'s`;
    user_num.textContent = data.users_count;
    if (notForMe(data)) {
      infodiv.innerHTML += `
      <div class="side-text">
      <p style="font-size:12px;">${esc(data.info)}</p>
      </div>
      `;
    }
    infodiv.scrollTop = infodiv.scrollHeight;
  }
  if (command === "clicked") {
    getLastStep(data.dataset);
    checkTurn();
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
    gamestate = "OFF";
    if (notForMe(data)) {
      Swal.fire({ title: "You Lost", text: data.info, icon: "error" }); // text, not HTML
    }
  }

  if (command === "chat") {
    infodiv.innerHTML += `<div class="side-text">
        <p >${esc(data.chat)}
        <span class="float-right"> - ${esc(data.user)}</span>
        </p>
     </div>
    `;
    infodiv.scrollTop = infodiv.scrollHeight;
  }
};
function checkTurn() {
  playerTrack === total_player - 1 ? (playerTrack = 0) : playerTrack++;
  currPlayer = allPlayers[playerTrack];
  userTurn.textContent =
    currPlayer === loc_username ? "Your " : `${currPlayer}'s`;
}

chatInput.addEventListener("keyup", (e) => {
  if (e.key === 13 || e.key === "Enter") {
    if (!chatInput.value.trim()) {
      return Swal.fire({
        icon: "error",
        title: "Oops...",
        text: "Your Message Cannot Be Empty !!",
        toast: true,
        position: "top-right",
      });
    }
    ws.send(
      JSON.stringify({
        user: loc_username,
        chat: chatInput.value,
        command: "chat",
      })
    );
    chatInput.value = "";
  }
});

function getLastStep(data) {
  const lastStepDiv = document.getElementById("lastStepDiv");
  lastStepDiv.innerHTML = `<span>Last Step : <span class="prevStep">${esc(data)}</span></span>`;
}

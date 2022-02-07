const infodiv = document.getElementById("infodiv");

const urls = "ws://127.0.0.1:8000/ws/clicked" + window.location.pathname;
const ws = new WebSocket(urls);
const addmearr = [];
const loc_username = localStorage.getItem("username");
ws.onopen = function (e) {
  console.log("connection open");

  ws.send(
    JSON.stringify({
      command: "joined",
      info: `${loc_username} just Joined `,
      user: loc_username,
    })
  );
};

ws.onerror = function (e) {
  console.log("error is ", e);
};
ws.onmessage = function (e) {
  const data = JSON.parse(e.data);
  const command = data.command;

  if (command === "clicked") {
 
    const clickedDiv = document.querySelector(
      `[data-innernum='${data.dataset}']`
    );
    if (data.user !== loc_username) {
      const myDataSetId = parseInt(clickedDiv.dataset.id);

      if (!addmearr.includes(myDataSetId)) {
        addmearr.push(myDataSetId);
        loopItemsAndCheck();
      }
    }
    clickedDiv.classList.add("clicked");
  }
  if (command === "won") {
    if (data.user !== loc_username) {
      Swal.fire("You Lost", data.info, "error");
    }
  }
  if (command === "joined") {
    if (data.user !== loc_username) {
      infodiv.innerHTML += `<p style="font-size:12px;">${data.info}</p>`;
    }
    var element = document.getElementById("sidebar");
    element.scrollIntoView({
      behavior: "smooth",
      block: "end",
      inline: "nearest",
    });
  }
};
ws.onclose = function (e) {
  ws.send(
    JSON.stringify({
      command: "left",
      user: loc_username,
    })
  );
};

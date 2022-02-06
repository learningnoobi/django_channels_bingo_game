const urls = "ws://127.0.0.1:8000/ws/clicked"+window.location.pathname;
const ws = new WebSocket(urls);
const addmearr = [];
ws.onopen = function (e) {
  console.log("connection open");
};
ws.onclose = function (e) {
  console.log("closed");
};
ws.onerror = function (e) {
  console.log("error is ", e);
};
ws.onmessage = function (e) {
  const data = JSON.parse(e.data);
 // console.log(data);
  const clickedDiv = document.querySelector(
    `[data-innernum='${data.dataset}']`
  );
  addmearr.push(data.dataset)
  console.log(addmearr)
 
  clickedDiv.classList.add("clicked");
};

var grid = document.querySelector(".grid");
const items = [...document.querySelector(".grid").children];
const bingodiv = document.querySelector("#bingodiv");
let keysArr = [];
window.onload = () => {
  restart();
};

//all possible combination for bingo 
const bingoItems = [
  [1, 2, 3, 4, 5],
  [6, 7, 8, 9, 10],
  [11, 12, 13, 14, 15],
  [16, 17, 18, 19, 20],
  [21, 22, 23, 24, 25],
  [1, 7, 13, 19, 25],
  [1, 6, 11, 16, 21],
  [2, 7, 12, 17, 22],
  [3, 8, 13, 18, 23],
  [4, 9, 14, 19, 24],
  [5, 10, 15, 20, 25],
  [5, 9, 13, 17, 21],
];

function GetRandomArray() {
  keysArr = [];
  for (let i = 1; i < 26; i++) {
    b = Math.ceil(Math.random() * 25);
    if (!keysArr.includes(b)) {
      keysArr.push(b);
    } else {
      i--;
    }
  }
}



const includesAll = (arr, values) => values.every((v) => arr.includes(v));

const bingoState = ["B", "I", "N", "G", "O"];

let bingoIndex = 0;

function fillGrid() {
  items.forEach((item, ind) => {
    item.innerHTML = keysArr[ind];
    item.dataset.innernum = keysArr[ind];


      item.addEventListener("click", (e) => {
           if(gamestate==="ON"){
      if(currPlayer ===loc_username){
        checkBingo(item);
      }
      else{
        Swal.fire({
          icon: 'error',
          title: 'Oops...',
          text: 'Not Your Turn!',
          toast:true,
          position: 'top-right',
        })
      }}
  else{
        Swal.fire({
          icon: 'error',
          title: 'Oops...',
          text: 'Game Finished ! Please Restart To Play Again !',

        })
      }
    })
   



  });
}


function restart() {
  GetRandomArray();
  fillGrid();
}

//when we click restart just refresh page
function refreshPage() {
  window.location.reload();
}


function checkBingo(item) {
  const dataid = item.dataset.id;
  const innernum = item.dataset.innernum;
  const dataint = parseInt(dataid)
  if (!addmearr.includes(dataint)) {
    addmearr.push(dataint);
     item.classList.add("clicked");
    ws.send(
      JSON.stringify({
        command: "clicked",
        dataset: innernum,
        dataid: dataid,
        user: loc_username,
      })
    );
    loopItemsAndCheck();
  }
  else{
       Swal.fire({
        icon: 'error',
        title: 'Oops...',
        text: 'Already Selected',
        toast:true,
        position: 'top-right',

        
      })
  }
 
}

function loopItemsAndCheck() {
  for (const j of bingoItems) {
    if (includesAll(addmearr, j)) {
      const index = bingoItems.indexOf(j);
      if (index > -1) {
        bingoItems.splice(index, 1);
      }

      let span = document.createElement("span");
      span.append(bingoState[bingoIndex]);
      bingodiv.append(span);
      bingoIndex += 1;
      if (bingoIndex === 5) {
        Swal.fire(loc_username, "You won the Game ", "success");
        ws.send(
          JSON.stringify({
            command: "won",
            user: loc_username,
            bingoCount:bingoIndex,
            info: `${loc_username} won the Game`,
          })
        );
      }
    }
  }
}


var grid = document.querySelector(".grid");


const items = [...document.querySelector(".grid").children];
const bingodiv = document.querySelector("#bingodiv");
let keysArr = [];
      window.onload = () => {
        restart();
      };

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

      function FillBingo() {
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
          item.dataset.innernum=keysArr[ind];
          item.addEventListener("click", (e) => {
            const dataid = item.dataset.id;
            const innernum = item.dataset.innernum;
            if (!addmearr.includes(dataid)) {
              addmearr.push(parseInt(dataid));
            }
            item.classList.add("clicked");
            ws.send(JSON.stringify({
              command:'clicked',
               dataset: innernum,
                user: "rayon" 
              }));
            for (const j of bingoItems) {
              if (includesAll(addmearr, j)) {
                const index = bingoItems.indexOf(j);
                if (index > -1) {
                  bingoItems.splice(index, 1);
                }

                let span = document.createElement("span");
                span.append(bingoState[bingoIndex]);
                bingodiv.append(span);

                bingodiv.append();
                bingoIndex += 1;
                if (bingoIndex === 5) {
                  Swal.fire("Rayon", "You really won boi", "success");
                }
              }
            }
          });
        });
      }

      function restart() {
        FillBingo();
        fillGrid();
      }

      function refreshPage() {
        window.location.reload();
      }
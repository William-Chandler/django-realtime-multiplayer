const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const socket = new WebSocket(`ws://${window.location.host}/ws/game/`);

let players = {};

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);

    // Handle disconnect event
    if (data.disconnect) {
        delete players[data.id];
        return;
    }

    // Handle normal movement / snapshot
    if (data.x !== undefined && data.y !== undefined) {
        players[data.id] = { x: data.x, y: data.y };
    }
};

document.addEventListener("mousemove", (e) => {
    socket.send(JSON.stringify({ x: e.clientX, y: e.clientY }));
});

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const id in players) {
        const p = players[id];
        ctx.beginPath();
        ctx.arc(p.x, p.y, 10, 0, 2 * Math.PI);
        ctx.fillStyle = "red";
        ctx.fill();
    }

    requestAnimationFrame(draw);
}

draw();

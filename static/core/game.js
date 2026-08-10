// =====================
// Load user config from JSON script tag
// =====================
const config = JSON.parse(
    document.getElementById("user-config").textContent
);
const USER_COLOUR = config.colour;

// =====================
// Canvas setup
// =====================
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
window.addEventListener("resize", resizeCanvas);
resizeCanvas();

// =====================
// WebSocket
// =====================
const socket = new WebSocket(`ws://${window.location.host}/ws/game/`);

// Force Chrome to close the WebSocket before navigating away
window.addEventListener("pagehide", () => {
    socket.close();
});

let players = {};

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);

    if (data.disconnect) {
        delete players[data.id];
        return;
    }

    if (data.x !== undefined && data.y !== undefined) {
        players[data.id] = {
            x: data.x,
            y: data.y,
            colour: data.colour || "red"
        };
    }
};

// =====================
// Mouse movement
// =====================
document.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    socket.send(JSON.stringify({
        x,
        y,
        colour: USER_COLOUR
    }));
});

// =====================
// Drawing loop
// =====================
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const id in players) {
        const p = players[id];
        ctx.beginPath();
        ctx.arc(p.x, p.y, 10, 0, 2 * Math.PI);
        ctx.fillStyle = p.colour;
        ctx.fill();
    }

    requestAnimationFrame(draw);
}

draw();

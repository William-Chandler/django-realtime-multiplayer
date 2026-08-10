const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
window.addEventListener("resize", resizeCanvas);
resizeCanvas();

const socket = new WebSocket(`ws://${window.location.host}/ws/game/`);

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
            colour: data.colour || "red"   // fallback
        };
    }
};

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

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const id in players) {
        const p = players[id];
        ctx.beginPath();
        ctx.arc(p.x, p.y, 10, 0, 2 * Math.PI);
        ctx.fillStyle = p.colour;   // ← use their colour
        ctx.fill();
    }

    requestAnimationFrame(draw);
}


draw();

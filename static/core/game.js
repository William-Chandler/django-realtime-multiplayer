// =====================
// Load user config from JSON script tag
// =====================
const config = JSON.parse(
    document.getElementById("user-config").textContent
);
const USER_COLOUR = config.colour;
const USER_DIAMETER = config.diameter || 10;

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
const socket = new WebSocket(`ws://${window.location.host}/ws/game/${room_id}/`);

// Debugging
console.log("Server says room is:", window.SERVER_ROOM_ID);
console.log("Client thinks room is:", room_id);

window.addEventListener("pagehide", () => socket.close());

let players = {};
let strokes = [];   // persistent drawing history

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);

    // Player disconnect
    if (data.disconnect) {
        delete players[data.id];
        return;
    }

    // Player movement
    if (data.x !== undefined && data.y !== undefined) {
        players[data.id] = {
            x: data.x,
            y: data.y,
            colour: data.colour || "red"
        };
    }

    // Single stroke segment
    if (data.stroke) {
        strokes.push(data.stroke);
    }

    // Full stroke history on connect
    if (data.strokes) {
        strokes = data.strokes;
    }
};

// =====================
// Drawing state
// =====================
let drawing = false;
let lastX = null;
let lastY = null;

// =====================
// Mouse movement
// =====================
document.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Always send cursor position
    socket.send(JSON.stringify({
        x,
        y,
        colour: USER_COLOUR
    }));

    // Drawing mode
    if (drawing) {
        if (lastX !== null && lastY !== null) {
            const stroke = {
                x1: lastX,
                y1: lastY,
                x2: x,
                y2: y,
                colour: USER_COLOUR,
                diameter: USER_DIAMETER
            };

            // Send to server
            socket.send(JSON.stringify({ stroke }));

            // Add locally for instant feedback
            strokes.push(stroke);
        }

        lastX = x;
        lastY = y;
    }
});

canvas.addEventListener("mousedown", () => {
    drawing = true;
    lastX = null;
    lastY = null;
});

canvas.addEventListener("mouseup", () => {
    drawing = false;
    lastX = null;
    lastY = null;
});

// Close the WebSocket on unload
window.addEventListener("beforeunload", () => {
    try { socket.close(); } catch (e) {}
});

// =====================
// Drawing loop
// =====================
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw persistent strokes
    for (const s of strokes) {
        ctx.strokeStyle = s.colour;
        ctx.lineWidth = s.diameter;
        ctx.lineCap = "round";

        ctx.beginPath();
        ctx.moveTo(s.x1, s.y1);
        ctx.lineTo(s.x2, s.y2);
        ctx.stroke();
    }

    // Draw player cursors
    for (const id in players) {
        const p = players[id];
        ctx.beginPath();
        ctx.arc(p.x, p.y, USER_DIAMETER / 2, 0, 2 * Math.PI);
        ctx.fillStyle = p.colour;
        ctx.fill();
    }

    requestAnimationFrame(draw);
}

draw();

// =====================
// Load user config
// =====================
const config = JSON.parse(document.getElementById("user-config").textContent);
const DEFAULT_COLOUR = "white";
const COLOUR = config.colour || DEFAULT_COLOUR;   // unified colour
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

socket.onopen = () => {
    // Register player immediately
    socket.send(JSON.stringify({ x: 0, y: 0, colour: COLOUR }));
};

window.addEventListener("pagehide", () => socket.close());

let players = {};
let strokes = [];

// =====================
// Incoming messages
// =====================
socket.onmessage = (e) => {
    const data = JSON.parse(e.data);

    // Disconnect
    if (data.disconnect) {
        delete players[data.id];
        return;
    }

    // Stroke (drawing or click-dot)
    if (data.stroke) {
        strokes.push(data.stroke);
        return;
    }

    // Full stroke history
    if (data.strokes) {
        strokes = data.strokes;
        return;
    }

    // Movement
    if (data.id && data.x !== undefined && data.y !== undefined) {
        players[data.id] = {
            x: data.x,
            y: data.y,
            colour: data.colour || COLOUR   // unified colour fallback
        };
    }
};

// =====================
// Drawing state
// =====================
let drawing = false;
let lastX = null;
let lastY = null;

// Helper: canvas-relative coords
function getCanvasCoords(e) {
    const rect = canvas.getBoundingClientRect();
    return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
    };
}

// =====================
// Click → dot stroke
// =====================
canvas.addEventListener("mousedown", (e) => {
    const { x, y } = getCanvasCoords(e);

    // Send dot stroke
    socket.send(JSON.stringify({
        draw: true,
        x,
        y,
        colour: COLOUR,
        diameter: USER_DIAMETER
    }));

    drawing = true;
    lastX = null;
    lastY = null;
});

canvas.addEventListener("mouseup", () => {
    drawing = false;
    lastX = null;
    lastY = null;
});

// =====================
// Movement + drawing
// =====================
document.addEventListener("mousemove", (e) => {
    const { x, y } = getCanvasCoords(e);

    // Always send movement
    socket.send(JSON.stringify({
        x,
        y,
        colour: COLOUR
    }));

    // Drawing mode
    if (drawing) {
        if (lastX !== null && lastY !== null) {
            const stroke = {
                x1: lastX,
                y1: lastY,
                x2: x,
                y2: y,
                colour: COLOUR,
                diameter: USER_DIAMETER
            };

            // Instant local feedback
            strokes.push(stroke);

            // Send to server
            socket.send(JSON.stringify({ stroke }));
        }

        lastX = x;
        lastY = y;
    }
});

// =====================
// Drawing loop
// =====================
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw strokes
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

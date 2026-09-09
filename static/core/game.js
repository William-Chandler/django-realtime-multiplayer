// =====================
// Load user config
// =====================
const config = JSON.parse(document.getElementById("user-config").textContent);
const DEFAULT_COLOUR = "white";
const COLOUR = config.colour || DEFAULT_COLOUR;
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
// WebSocket + helpers
// =====================
let players = {};
let strokes = [];

const socket = new WebSocket(`ws://${window.location.host}/ws/game/${room_id}/`);

function send(data) {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(data));
    }
}

socket.onopen = () => {
    // Register player immediately
    send({
        x: 0,
        y: 0,
        colour: COLOUR,
        diameter: USER_DIAMETER
    });

    // Create local player instantly
    players["local"] = {
        tx: 0, ty: 0,
        ix: 0, iy: 0,
        colour: COLOUR,
        diameter: USER_DIAMETER
    };
};

window.addEventListener("pagehide", () => socket.close());


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

    // Stroke
    if (data.stroke) {
        strokes.push(data.stroke);
        return;
    }

    // Full stroke history
    if (data.strokes) {
        strokes = data.strokes;
        return;
    }

    // Movement with interpolation
    if (data.id && data.x !== undefined && data.y !== undefined) {
        let p = players[data.id];

        if (!p) {
            p = players[data.id] = {
                x: data.x,
                y: data.y,
                tx: data.x,
                ty: data.y,
                ix: data.x,
                iy: data.y,
                colour: data.colour || COLOUR,
                diameter: data.diameter || USER_DIAMETER
            };
        } else {
            p.tx = data.x;
            p.ty = data.y;

            if (data.diameter !== undefined) {
                p.diameter = data.diameter;
            }
        }
    }
};


// =====================
// Drawing state
// =====================
let drawing = false;
let lastX = null;
let lastY = null;

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

    send({
        draw: true,
        x,
        y,
        colour: COLOUR,
        diameter: USER_DIAMETER
    });

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
let lastSent = 0;
const MOVEMENT_INTERVAL = 16; // 60 per second

document.addEventListener("mousemove", (e) => {
    const { x, y } = getCanvasCoords(e);

    const now = performance.now();
    if (now - lastSent >= MOVEMENT_INTERVAL) {
        send({
            x,
            y,
            colour: COLOUR,
            diameter: USER_DIAMETER
        });
        lastSent = now;
    }

    if (players["local"]) {
        players["local"].tx = x;
        players["local"].ty = y;
        players["local"].diameter = USER_DIAMETER;
    }

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

            strokes.push(stroke);
            send({ stroke });
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

    for (const s of strokes) {
        ctx.strokeStyle = s.colour;
        ctx.lineWidth = s.diameter;
        ctx.lineCap = "round";

        ctx.beginPath();
        ctx.moveTo(s.x1, s.y1);
        ctx.lineTo(s.x2, s.y2);
        ctx.stroke();
    }

    const INTERPOLATION_SPEED = 0.15;

    for (const id in players) {
        const p = players[id];
        p.ix += (p.tx - p.ix) * INTERPOLATION_SPEED;
        p.iy += (p.ty - p.iy) * INTERPOLATION_SPEED;
    }

    for (const id in players) {
        const p = players[id];
        ctx.beginPath();
        ctx.arc(p.ix, p.iy, p.diameter / 2, 0, 2 * Math.PI);
        ctx.fillStyle = p.colour;
        ctx.fill();
    }

    requestAnimationFrame(draw);
}

draw();
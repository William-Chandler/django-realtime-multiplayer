// game.testable.js

export function interpolate(p, speed = 0.15) {
    p.ix += (p.tx - p.ix) * speed;
    p.iy += (p.ty - p.iy) * speed;
    return p;
}

export function handleIncomingMessage(players, strokes, data, defaults) {
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
        return strokes;
    }

    // Movement
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
                colour: data.colour || defaults.colour,
                diameter: data.diameter || defaults.diameter
            };
        } else {
            p.tx = data.x;
            p.ty = data.y;

            if (data.diameter !== undefined) {
                p.diameter = data.diameter;
            }
        }
    }

    return strokes;
}

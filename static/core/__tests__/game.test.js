import { interpolate, handleIncomingMessage } from "../game.testable.js";

describe("interpolation", () => {
    test("moves ix/iy toward tx/ty", () => {
        const p = { ix: 0, iy: 0, tx: 10, ty: 20 };
        const updated = interpolate(p, 0.1);

        expect(updated.ix).toBeCloseTo(1);
        expect(updated.iy).toBeCloseTo(2);
    });
});

describe("handleIncomingMessage", () => {
    let players;
    let strokes;
    const defaults = { colour: "white", diameter: 10 };

    beforeEach(() => {
        players = {};
        strokes = [];
    });

    test("creates a new player on movement", () => {
        handleIncomingMessage(players, strokes, {
            id: "abc",
            x: 50,
            y: 60
        }, defaults);

        expect(players["abc"]).toBeDefined();
        expect(players["abc"].tx).toBe(50);
        expect(players["abc"].ty).toBe(60);
    });

    test("updates existing player movement", () => {
        players["abc"] = {
            tx: 0, ty: 0,
            ix: 0, iy: 0,
            diameter: 10
        };

        handleIncomingMessage(players, strokes, {
            id: "abc",
            x: 100,
            y: 200
        }, defaults);

        expect(players["abc"].tx).toBe(100);
        expect(players["abc"].ty).toBe(200);
    });

    test("updates diameter when provided", () => {
        players["abc"] = {
            tx: 0, ty: 0,
            ix: 0, iy: 0,
            diameter: 10
        };

        handleIncomingMessage(players, strokes, {
            id: "abc",
            x: 100,
            y: 200,
            diameter: 30
        }, defaults);

        expect(players["abc"].diameter).toBe(30);
    });

    test("adds a stroke", () => {
        handleIncomingMessage(players, strokes, {
            stroke: { x1: 1, y1: 2, x2: 3, y2: 4 }
        }, defaults);

        expect(strokes.length).toBe(1);
        expect(strokes[0]).toEqual({ x1: 1, y1: 2, x2: 3, y2: 4 });
    });

    test("replaces full stroke history", () => {
        const newStrokes = [
            { x1: 1, y1: 1, x2: 2, y2: 2 },
            { x1: 3, y1: 3, x2: 4, y2: 4 }
        ];

        const result = handleIncomingMessage(players, strokes, {
            strokes: newStrokes
        }, defaults);

        expect(result).toEqual(newStrokes);
    });

    test("removes player on disconnect", () => {
        players["abc"] = { tx: 0, ty: 0 };
        handleIncomingMessage(players, strokes, {
            disconnect: true,
            id: "abc"
        }, defaults);

        expect(players["abc"]).toBeUndefined();
    });
});

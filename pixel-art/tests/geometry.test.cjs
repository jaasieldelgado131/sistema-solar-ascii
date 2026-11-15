const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function load(file) {
    const context = {};
    vm.createContext(context);
    const source = fs.readFileSync(__dirname + '/../contents/ui/' + file, 'utf8').replace(/^\.pragma library$/m, '');
    vm.runInContext(source, context);
    return context;
}
const geo = load('Geometry.js');
const atlas = load('Atlas.js').data;

test('eight planets with sprites, distinct orbits and periodic motion', () => {
    assert.equal(geo.planets.length, 8);
    assert.equal(new Set(geo.planets.map(p => p.orbit)).size, 8);
    for (const planet of geo.planets) {
        assert.ok(atlas.bodies[planet.key], planet.key);
        assert.ok(atlas.labels[planet.key], planet.key);
        const a = geo.planetState(planet, 0, 1);
        const b = geo.planetState(planet, planet.period, 1);
        const half = geo.planetState(planet, planet.period / 2, 1);
        assert.ok(Math.hypot(a.x - b.x, a.y - b.y) < 1e-6);
        assert.ok(Math.hypot(a.x - half.x, a.y - half.y) > 40);
    }
});

test('sprite frames stay inside their atlas', () => {
    assert.equal(atlas.rotFrames, geo.rotFrames);
    assert.equal(atlas.lightFrames, geo.lightFrames);
    for (const planet of geo.planets) {
        for (let t = 0; t < 600; t += 0.37) {
            const s = geo.planetState(planet, t, 1);
            assert.ok(Number.isInteger(s.frame) && s.frame >= 0 && s.frame < atlas.bodies[planet.key].cols);
            assert.ok(Number.isInteger(s.light) && s.light >= 0 && s.light < atlas.bodies[planet.key].rows);
        }
    }
});

test('light rows follow the orbit: far side lit, near side in crescent', () => {
    // Behind the Sun (top of the ellipse) the planet faces us fully lit: row 24 of 32.
    assert.equal(geo.lightIndex(-Math.PI / 2), 24);
    assert.equal(geo.lightIndex(Math.PI / 2), 8);
    assert.equal(geo.lightIndex(Math.PI * 2 - 0.001), 0);
});

test('whole system fits the art canvas on common screens', () => {
    for (const [w, h] of [[1920, 1200], [1920, 1080], [1366, 768], [2560, 1440], [3840, 2160], [1080, 1920], [800, 600]]) {
        const px = geo.autoPixel(w, h);
        const aw = Math.ceil(w / px), ah = Math.ceil(h / px);
        const layout = geo.layout(aw, ah);
        for (let angle = 0; angle < Math.PI * 2; angle += 0.02) {
            const p = geo.orbitPoint(geo.outerOrbit * layout.scale, angle);
            const x = layout.x + p.x, y = layout.y + p.y;
            assert.ok(x > 4 && x < aw - 4, `x clipped at ${w}x${h}`);
            assert.ok(y > 4 && y < ah - 4, `y clipped at ${w}x${h}`);
        }
    }
});

test('comet follows Kepler and swings close to the Sun', () => {
    let closest = Infinity;
    for (let t = 0; t < geo.comet.period; t += 0.05) {
        const c = geo.cometState(t, 1);
        assert.ok(Number.isFinite(c.x) && Number.isFinite(c.y));
        assert.ok(c.tail >= 3 && c.tail <= 38);
        assert.ok(Math.abs(Math.hypot(c.dx, c.dy) - 1) < 1e-9);
        closest = Math.min(closest, c.distance);
    }
    assert.ok(Math.abs(closest - geo.comet.perihelion) < 1, `perihelion ${closest}`);
});

test('shooting stars stay bounded and move', () => {
    for (let t = 0; t < 200; t += 0.1) {
        for (let index = 0; index < 2; index++) {
            const m = geo.meteor(index, t, 640, 400);
            assert.ok(Number.isFinite(m.x) && Number.isFinite(m.y));
            assert.ok(m.opacity >= 0 && m.opacity <= 1);
            assert.ok(m.dir === 1 || m.dir === -1);
        }
    }
});

test('rocket leaves Earth, reaches Mars and comes back', () => {
    const m = geo.mission;
    const start = geo.missionState(m.offset + 0.001, 1);
    const end = geo.missionState(m.offset + m.flight - 0.001, 1);
    const earth = geo.planetState(geo.planets[2], m.offset, 1);
    const mars = geo.planetState(geo.planets[3], m.offset + m.flight, 1);
    assert.ok(Math.hypot(start.x - earth.x, start.y - earth.y) < 1);
    assert.ok(Math.hypot(end.x - mars.x, end.y - mars.y) < 1);
    assert.equal(geo.missionState(m.offset + m.flight + 5, 1).visible, false);
    const back = geo.missionState(m.offset + m.cycle + m.flight - 0.001, 1);
    const earthLater = geo.planetState(geo.planets[2], m.offset + m.cycle + m.flight, 1);
    assert.ok(Math.hypot(back.x - earthLater.x, back.y - earthLater.y) < 1);
    for (let t = m.offset; t < m.offset + m.flight; t += 0.2) {
        const s = geo.missionState(t, 1);
        assert.ok(s.dir >= 0 && s.dir < atlas.ship.cols && Number.isInteger(s.dir));
    }
});

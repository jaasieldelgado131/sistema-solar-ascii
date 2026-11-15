const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const scene = {};
vm.createContext(scene);
vm.runInContext(fs.readFileSync(__dirname + '/../contents/ui/Space.js', 'utf8'), scene);

test('all eight planets have distinct orbits and complete a revolution', () => {
    assert.equal(scene.planets.length, 8);
    assert.equal(new Set(scene.planets.map(p => p.orbit)).size, 8);
    for (const planet of scene.planets) {
        const a = scene.planetPosition(planet, 0);
        const b = scene.planetPosition(planet, planet.period);
        const half = scene.planetPosition(planet, planet.period / 2);
        assert.ok(Math.hypot(a.x - b.x, a.y - b.y) < 1e-8);
        assert.ok(Math.hypot(a.x - half.x, a.y - half.y) > 100);
    }
});

test('complete outer orbit fits common landscape and portrait displays', () => {
    for (const [w, h] of [[1920,1200], [1366,768], [3840,2160], [1080,1920], [800,600]]) {
        const layout = scene.layout(w, h);
        for (let angle = 0; angle < Math.PI * 2; angle += 0.02) {
            const p = scene.orbitPoint(810, angle);
            const x = layout.x + p.x * layout.scale;
            const y = layout.y + p.y * layout.scale;
            assert.ok(x > 24 && x < w - 24, `x clipped at ${w}x${h}`);
            assert.ok(y > 24 && y < h - 24, `y clipped at ${w}x${h}`);
        }
    }
});

test('meteor showers repeat, remain bounded, and change position', () => {
    for (let t = 0; t < 200; t += 0.1) {
        for (let index = 0; index < 3; index++) {
            const m = scene.meteor(index, t, 1920, 1200);
            assert.ok(Number.isFinite(m.x) && Number.isFinite(m.y));
            assert.ok(m.opacity >= 0 && m.opacity <= 1);
            assert.ok(m.progress >= 0 && m.progress < 1);
        }
    }
    assert.notEqual(scene.meteor(0, 1, 1920, 1200).x, scene.meteor(0, 2, 1920, 1200).x);
});

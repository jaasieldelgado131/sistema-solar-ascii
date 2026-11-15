.pragma library
// Geometría determinista. Distancias en píxeles del arte; tiempo en segundos artísticos.
// SQUASH y TILT deben coincidir con tools/generate_pixel_art.py (la luz de los sprites).

var tau = Math.PI * 2;
var squash = 0.44;
var tilt = -0.12;
var rotFrames = 64;
var lightFrames = 32;
var outerOrbit = 302;

// spin: segundos por vuelta sobre su eje (ya incluye el sentido en los sprites).
var planets = [
    {key: "mercurio", orbit: 50,  period: 38,  phase: 2.8,  spin: 40},
    {key: "venus",    orbit: 70,  period: 61,  phase: 4.9,  spin: 70},
    {key: "tierra",   orbit: 95,  period: 88,  phase: 0.5,  spin: 16},
    {key: "marte",    orbit: 120, period: 124, phase: 3.8,  spin: 17},
    {key: "jupiter",  orbit: 180, period: 202, phase: 5.65, spin: 9},
    {key: "saturno",  orbit: 228, period: 286, phase: 2.6,  spin: 10},
    {key: "urano",    orbit: 268, period: 378, phase: 4.2,  spin: 13},
    {key: "neptuno",  orbit: 302, period: 470, phase: 0.18, spin: 12}
];

function mod(a, n) {
    return ((a % n) + n) % n;
}

function hash(n) {
    var f = Math.sin(n * 127.1 + 311.7) * 43758.5453;
    return f - Math.floor(f);
}

// Punto del plano orbital (x, y) proyectado en pantalla.
function project(x, y) {
    var sy = y * squash;
    return {x: x * Math.cos(tilt) - sy * Math.sin(tilt),
            y: x * Math.sin(tilt) + sy * Math.cos(tilt)};
}

function orbitPoint(radius, angle) {
    return project(Math.cos(angle) * radius, Math.sin(angle) * radius);
}

// Índice de iluminación: qué fila del atlas mira hacia el Sol.
function lightIndex(angle) {
    return Math.round(mod(angle, tau) / tau * lightFrames) % lightFrames;
}

function spinFrame(spinSeconds, seconds) {
    return mod(Math.floor(seconds / spinSeconds * rotFrames), rotFrames);
}

function planetState(planet, seconds, scale) {
    var angle = planet.phase + seconds * tau / planet.period;
    var p = orbitPoint(planet.orbit * scale, angle);
    return {x: p.x, y: p.y, z: Math.sin(angle) * planet.orbit,
            light: lightIndex(angle), frame: spinFrame(planet.spin, seconds)};
}

// Tamaño del píxel: unos 640x400 píxeles de arte en cualquier pantalla.
function autoPixel(physicalWidth, physicalHeight) {
    return Math.max(1, Math.round(Math.min(physicalWidth / 640, physicalHeight / 400)));
}

function layout(width, height) {
    var vertical = Math.sqrt(Math.pow(Math.sin(tilt), 2) + Math.pow(squash * Math.cos(tilt), 2));
    var scale = Math.min((width / 2 - 14) / (outerOrbit + 10), (height / 2 - 24) / (outerOrbit * vertical + 12));
    return {x: Math.round(width / 2), y: Math.round(height / 2 + 4),
            scale: Math.max(0.35, Math.min(1.8, scale))};
}

// Satélite alrededor de un planeta: desplazamiento local y si pasa por delante.
function moon(radius, period, phase, seconds) {
    var a = phase + seconds * tau / period;
    var p = orbitPoint(radius, a);
    return {x: p.x, y: p.y, front: Math.sin(a) > 0, light: lightIndex(a)};
}

// Cometa en órbita kepleriana muy excéntrica; el Sol ocupa un foco.
var comet = {perihelion: 54, eccentricity: 0.9, period: 150, omega: 2.35, offset: 40};

function cometState(seconds, scale) {
    var e = comet.eccentricity;
    var a = comet.perihelion / (1 - e);
    var M = mod((seconds + comet.offset) / comet.period, 1) * tau - Math.PI;   // empieza lejos del Sol
    var E = M;
    for (var i = 0; i < 12; i++)
        E -= (E - e * Math.sin(E) - M) / (1 - e * Math.cos(E));
    var px = a * (Math.cos(E) - e), py = a * Math.sqrt(1 - e * e) * Math.sin(E);
    var x = px * Math.cos(comet.omega) - py * Math.sin(comet.omega);
    var y = px * Math.sin(comet.omega) + py * Math.cos(comet.omega);
    var s = project(x * scale, y * scale);
    var r = Math.sqrt(px * px + py * py);
    var len = Math.sqrt(s.x * s.x + s.y * s.y) || 1;
    return {x: s.x, y: s.y, z: y, distance: r, dx: s.x / len, dy: s.y / len,
            tail: Math.round(Math.max(3, Math.min(38, 2300 / r)))};
}

// Estrella fugaz: trazo 2:1 limpio en píxeles; dir es +1 o -1.
function meteor(index, seconds, width, height) {
    var cycle = 9 + index * 5.3;
    var clock = seconds + index * 3.7 + 2.1;
    var generation = Math.floor(clock / cycle);
    var age = clock - generation * cycle;
    var duration = 1.15;
    var travel = age / duration;
    var dir = hash(generation * 5 + index * 11) > 0.5 ? 1 : -1;
    var distance = 120 + hash(generation * 3 + index) * 90;
    var x0 = width * (0.15 + hash(generation * 7 + index * 33) * 0.7) - dir * distance * 0.5;
    var y0 = height * (0.04 + hash(generation * 13 + index * 17) * 0.35);
    return {x: Math.round(x0 + dir * distance * travel), y: Math.round(y0 + distance * travel / 2),
            dir: dir, visible: travel < 1,
            opacity: Math.max(0, Math.min(1, travel * 6, (1 - travel) * 3))};
}

// Misión de la nave: ida Tierra -> Marte y vuelta, cada `cycle` segundos.
var mission = {cycle: 140, flight: 26, offset: 34};

function missionState(seconds, scale) {
    var clock = seconds - mission.offset;
    var n = Math.floor(clock / mission.cycle);
    var t0 = n * mission.cycle + mission.offset;
    var s = (seconds - t0) / mission.flight;
    if (clock < 0 || s < 0 || s > 1)
        return {visible: false, x: 0, y: 0, dir: 0, trail: []};
    var earth = planets[2], mars = planets[3];
    var from = planetState(n % 2 === 0 ? earth : mars, t0, scale);
    var to = planetState(n % 2 === 0 ? mars : earth, t0 + mission.flight, scale);
    var mx = (from.x + to.x) / 2, my = (from.y + to.y) / 2;
    var nx = -(to.y - from.y), ny = to.x - from.x;
    if (nx * mx + ny * my < 0) { nx = -nx; ny = -ny; }   // el arco se abre lejos del Sol
    var cx = mx + nx * 0.35, cy = my + ny * 0.35;
    function at(u) {
        var e = 0.5 - 0.5 * Math.cos(Math.PI * Math.max(0, Math.min(1, u)));
        var a = (1 - e) * (1 - e), b = 2 * (1 - e) * e, c = e * e;
        return {x: a * from.x + b * cx + c * to.x, y: a * from.y + b * cy + c * to.y};
    }
    var p = at(s), q = at(s + 0.01);
    var heading = Math.atan2(-(q.y - p.y), q.x - p.x);
    var trail = [];
    for (var k = 1; k <= 6; k++) {
        var tp = at(s - k * 0.012);
        trail.push({x: Math.round(tp.x), y: Math.round(tp.y)});
    }
    return {visible: s > 0.02 && s < 0.98, x: p.x, y: p.y, trail: trail,
            dir: mod(Math.round(heading / tau * 16), 16)};
}

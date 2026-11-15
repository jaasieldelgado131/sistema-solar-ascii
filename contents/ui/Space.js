// Shared, deterministic geometry. Times are artistic seconds, distances design pixels.
var tau = Math.PI * 2;
var planets = [
    {name: "MERCURIO", orbit: 142, radius: 11, period: 38, phase: 2.8, color: "#b8b2aa", kind: 0},
    {name: "VENUS", orbit: 212, radius: 18, period: 61, phase: 4.9, color: "#edc995", kind: 1},
    {name: "TIERRA", orbit: 285, radius: 23, period: 88, phase: 0.5, color: "#6bbde5", kind: 2},
    {name: "MARTE", orbit: 356, radius: 16, period: 124, phase: 3.8, color: "#e38d72", kind: 3},
    {name: "JUPITER", orbit: 470, radius: 47, period: 202, phase: 5.65, color: "#dfb38a", kind: 4},
    {name: "SATURNO", orbit: 595, radius: 36, period: 286, phase: 2.6, color: "#e4c998", kind: 5},
    {name: "URANO", orbit: 705, radius: 27, period: 378, phase: 4.2, color: "#8bd5d2", kind: 6},
    {name: "NEPTUNO", orbit: 810, radius: 25, period: 470, phase: 0.18, color: "#789fe9", kind: 7}
];

function orbitPoint(radius, angle) {
    var x = Math.cos(angle) * radius;
    var y = Math.sin(angle) * radius * 0.52;
    var tilt = -0.20;
    return {x: x * Math.cos(tilt) - y * Math.sin(tilt),
            y: x * Math.sin(tilt) + y * Math.cos(tilt)};
}

function planetPosition(planet, seconds) {
    return orbitPoint(planet.orbit, planet.phase + seconds * tau / planet.period);
}

function layout(width, height) {
    return {x: width * 0.52, y: height * 0.53,
            scale: Math.max(0.01, Math.min((width - 100) / 1830, (height - 180) / 1080))};
}

function hash(n) {
    var f = Math.sin(n * 127.1 + 311.7) * 43758.5453;
    return f - Math.floor(f);
}

function meteor(index, seconds, width, height) {
    var cycle = 12 + index * 4.3;
    var clock = seconds + index * 5.1 + 1.8;
    var generation = Math.floor(clock / cycle);
    var age = clock - generation * cycle;
    var progress = age / cycle;
    var duration = 2.6;
    var travel = age / duration;
    return {x: width * (-0.18 + hash(generation * 7 + index * 33) * 0.75 + travel * 0.95),
            y: height * (-0.12 + hash(generation * 13 + index * 17) * 0.32 + travel * 0.65),
            opacity: Math.max(0, Math.min(1, travel * 7, (1 - travel) * 4)),
            progress: progress};
}

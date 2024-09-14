window.addEventListener("channel_ready", function (event) {

     event.detail.channel.addEventListener("code_set_robot_pos", function(event) {
         setRobotPos(event.detail.x, event.detail.y);
    });

     event.detail.channel.addEventListener("code_chart", function(event) {
         drawChart(event.detail.zones, event.detail.points);
    });

     event.detail.channel.addEventListener("code_robot_path", function(event) {
         drawPath(event.detail.points);
    });

});

svg = null;

const MAP_WIDTH = 900;
const MAP_HEIGHT = 260;
const MAP_PADDING = 10;

const ZERO_X = 150;
const ZERO_Y = MAP_HEIGHT / 2;

const ROBOT_WIDTH = 88;
const ROBOT_HEIGHT = 26;

const GRAY_MAIN = "#757575";
const GRAY_SUB = "#303030";
const RED = "#FF5050";

window.addEventListener("load", function() {
    svg = document.getElementById('chartRoot');

    setViewBox(0, 0, MAP_WIDTH + MAP_PADDING * 2, MAP_HEIGHT + MAP_PADDING * 2);

    drawBorder();

    drawZero();

    addChart();

    addPath();

    addRobot(0, 0);
});


function createSVGElement(tag, attrs) {
    const elem = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (let attr in attrs) {
        elem.setAttribute(attr, attrs[attr]);
    }
    return elem;
}

// Функция для настройки viewBox (масштабирование и смещение начала координат)
function setViewBox(x, y, width, height) {
    svg.setAttribute('viewBox', `${x} ${y} ${width} ${height}`);
}

function drawBorder() {
    const border = createSVGElement("rect", {
        id: "border",
        x: MAP_PADDING,
        y: MAP_PADDING,
        width: MAP_WIDTH,
        height: MAP_HEIGHT,
        rx: 6,
        opacity: "undefined",
        stroke: GRAY_MAIN,
        "fill-opacity": "0",
    });
    svg.appendChild(border);
}

function toSVGPos(x, y) {
    return [ZERO_X + x + MAP_PADDING, ZERO_Y - y + MAP_PADDING];
}

function drawZero() {
    var [svg_x, svg_y] = toSVGPos(0, 0);

    const zeroGroup = createSVGElement("g", {
        id: "zero",
        "fill-opacity": 0,
        "stroke-width": 1,
        stroke: GRAY_SUB,
    });

    const zeroVert = createSVGElement("line", {
        id: "zero_vert",
        x1: svg_x,
        y1: svg_y - 15,
        x2: svg_x,
        y2: svg_y + 15,
    })
    zeroGroup.append(zeroVert);

    const zeroHoriz = createSVGElement("line", {
        id: "zero_horiz",
        x1: svg_x - 15,
        y1: svg_y,
        x2: svg_x + 15,
        y2: svg_y,
    })
    zeroGroup.append(zeroHoriz);

    svg.append(zeroGroup);
}

function addRobot(x, y) {
    const [svg_x, svg_y] = toSVGPos(x, y);

    const robot = createSVGElement("svg", {
        id: "robot",
        x: svg_x - ROBOT_WIDTH / 2,
        y: svg_y - ROBOT_HEIGHT / 2,
    });

    const robotMain = createSVGElement("rect", {
        id: "robot_main",
        x: 0,
        y: 0,
        width: ROBOT_WIDTH,
        height: ROBOT_HEIGHT,
        rx: 10,
        stroke: GRAY_MAIN,
        fill: GRAY_SUB
    })
    robot.append(robotMain);

    const robotHead = createSVGElement("ellipse", {
        id: "robot_head",
        cx: ROBOT_WIDTH / 2,
        cy: ROBOT_HEIGHT * 0.3,
        rx: 4,
        ry: 4,
        stroke: GRAY_MAIN,
        fill: GRAY_SUB
    })
    robot.append(robotHead);

    svg.append(robot);
}

function setRobotPos(x, y) {
    const [svg_x, svg_y] = toSVGPos(x, y);
    const robot = document.getElementById("robot");
    robot.setAttribute("x", svg_x - ROBOT_WIDTH / 2);
    robot.setAttribute("y", svg_y - ROBOT_HEIGHT / 2);
}

function addChart() {
    const zonesGroup = createSVGElement("g", {
        id: "zones",
    });
    svg.append(zonesGroup);

    const pointsGroup = createSVGElement("g", {
        id: "points",
    });
    svg.append(pointsGroup);
}

function drawChart(zones, points) {
    const zonesGroup = document.getElementById("zones");
    for (let i = 0; i < zonesGroup.children.length; i++) {
        zonesGroup.children[0].remove()
    }

    const pointsGroup = document.getElementById("points");
    for (let i = 0; i < pointsGroup.children.length; i++) {
        pointsGroup.children[0].remove()
    }

    zones.forEach((z) => {
            const zoneSvg = produceZone(z);

            if (zoneSvg !== null) {
                zonesGroup.append(zoneSvg);
            }
        }
    )

    points.forEach((p) => {
            const pointSvg = producePoint(p);

            if (pointSvg !== null) {
                pointsGroup.append(pointSvg);
            }
        }
    )
}

function produceZone(zone) {
    if (zone.id === "passage") {
        const p0 = toSVGPos(zone.p0[0], zone.p0[1]);
        const p1 = toSVGPos(zone.p1[0], zone.p1[1]);
        const width = p1[0] - p0[0];
        const height = p1[1] - p0[1];
        return createSVGElement("rect", {
            id: "zone_passage",
            x: p0[0],
            y: p0[1],
            width: width,
            height: height,
            rx: 2,
            opacity: "undefined",
            stroke: GRAY_SUB,
            "fill-opacity": "0",
        });
    }
    return null;
}

function producePoint(point) {
    if (point.id.includes("seat")) {
        return produceSeat(point);
    }
    else if (point.id.includes("marker")) {
        return produceMarker(point);
    }
}

function produceSeat(point) {
    const [x, y] = toSVGPos(point.x, point.y);
    const seatNum = point.id.substring(5);
    const group = createSVGElement("g", {
        id: "seat_" + seatNum
    });

    const border = createSVGElement("rect", {
        x: x - 25,
        y: y - 25,
        width: 50,
        height: 50,
        rx: 6,
        stroke: GRAY_MAIN,
        fill: GRAY_SUB
    });
    group.append(border);

    const text = createSVGElement("text", {
        x: x,
        y: y,
        "dominant-baseline": "middle",
        "text-anchor": "middle",
        fill: GRAY_MAIN,
        "font-size": 30,
    });
    text.textContent = seatNum;
    group.append(text);

    return group;
}

function produceMarker(point) {
    const [x, y] = toSVGPos(point.x, point.y);

    const [_, side, num] = point.id.split("_");

    const group = createSVGElement("g", {
        id: "marker_" + side + "_" + num
    });

    const line = createSVGElement("line", {
        x1: x - 10,
        y1: y,
        x2: x + 10,
        y2: y,
        "stroke-width": 2,
        stroke: RED
    })
    group.append(line);

    const bin = (Number(num) >>> 0).toString(2);
    const valueCenter = y > 0 ? y - 10 : y + 10;

    group.append(createSVGElement("rect", {
        x: x - 9,
        y: valueCenter - 9,
        width: 18,
        height: 18,
        stroke: RED,
        "stroke-width": 0.7,
        "stroke-opacity": 0.6,
        fill: "none"
    }));

    if (bin[bin.length - 1] === "1") {
        group.append(createSVGElement("rect", {
            x: x - 8,
            y: valueCenter - 8,
            width: 8,
            height: 8,
            fill: RED
        }));
    }
    console.log(bin, bin[bin.length - 1], bin[bin.length - 2])
    if (bin[bin.length - 2] === "1") {
        group.append(createSVGElement("rect", {
            x: x,
            y: valueCenter - 8,
            width: 8,
            height: 8,
            fill: RED
        }));
    }
    if (bin[bin.length - 3] === "1") {
        group.append(createSVGElement("rect", {
            x: x - 8,
            y: valueCenter,
            width: 8,
            height: 8,
            fill: RED
        }));
    }
    if (bin[bin.length - 4] === "1") {
        group.append(createSVGElement("rect", {
            x: x,
            y: valueCenter,
            width: 8,
            height: 8,
            fill: RED
        }));
    }

    return group;
}

function addPath() {
    const pathGroup = createSVGElement("g", {
        id: "robot_path"
    });
    svg.append(pathGroup);
}

function drawPath(points) {
    const pathGroup = document.getElementById("robot_path");
    for (let i = 0; i < pathGroup.children.length; i++) {
        pathGroup.children[0].remove()
    }

    if (points.length === 0) {
        return;
    }

    const pointsSVG = [];
    points.forEach((point) => {
        const [x, y] = toSVGPos(point[0], point[1]);
        pointsSVG.push(`${x},${y}`);
    });

    const path = createSVGElement("polyline", {
        points: pointsSVG.join(" "),
        fill: "none",
        stroke: RED,
        "stroke-opacity": 0.6,
        "stroke-dasharray": "4"
    });
    pathGroup.append(path);

    const start = toSVGPos(points[0][0], points[0][1]);
    const startCircle = createSVGElement("ellipse", {
        cx: start[0],
        cy: start[1],
        rx: 4,
        ry: 4,
        stroke: RED,
        fill: "none"
    });
    pathGroup.append(startCircle);

    const stop = toSVGPos(points[points.length - 1][0], points[points.length - 1][1]);
    const stopCircle = createSVGElement("ellipse", {
        cx: stop[0],
        cy: stop[1],
        rx: 4,
        ry: 4,
        stroke: RED,
        fill: "none"
    });
    pathGroup.append(stopCircle);
}


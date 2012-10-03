// http://paulirish.com/2011/requestanimationframe-for-smart-animating/
(function() {
    var lastTime = 0;
    var vendors = ['ms', 'moz', 'webkit', 'o'];
    for(var x = 0; x < vendors.length && !window.requestAnimationFrame; ++x) {
        window.requestAnimationFrame = window[vendors[x]+'RequestAnimationFrame'];
        window.cancelAnimationFrame =
            window[vendors[x]+'CancelAnimationFrame'] || window[vendors[x]+'CancelRequestAnimationFrame'];
    }

    if (!window.requestAnimationFrame)
        window.requestAnimationFrame = function(callback, element) {
            var currTime = new Date().getTime();
            var timeToCall = Math.max(0, 16 - (currTime - lastTime));
            var id = window.setTimeout(function() { callback(currTime + timeToCall); },
                                       timeToCall);
            lastTime = currTime + timeToCall;
            return id;
        };

    if (!window.cancelAnimationFrame)
        window.cancelAnimationFrame = function(id) {
            clearTimeout(id);
        };
}());

function drawAxis(scale, g, x, y, orientation) {
    var color = d3.rgb(50,50,50);
    var strokeWidth = 0.5;
    var axis = d3.svg.axis()
        .scale(scale)
        .orient(orientation)
        .ticks(10)
        .tickSize(2);
    g.call(axis);
    g.attr("transform", "translate(" + x + "," + y + ")");
    g.selectAll("text")
        .attr("stroke", color)
        .attr("stroke-width", strokeWidth)
        .attr("font-size", 10);
    g.selectAll("path")
        .attr('fill', color)
        .attr('stroke-width', strokeWidth)
        .attr('stroke', 'none');
    return axis;
}

function drawCircles(g, xscale, yscale, xvalues, yvalues) {
    var pts = g.selectAll('circle').data(xvalues).enter();
    pts.append('circle')
        .attr('cx', function(value) {
            return xscale(value);
        })
        .attr('cy', function(value, index) {
            var value = yvalues[index];
            if (!$.isNumeric(value)) return -100;
            return yscale(value);
        })
        .attr('r', 1.5)
        .attr('fill', d3.rgb(0,100,200));
}

function drawPath(g, xscale, yscale, xvalues, yvalues) {
    var line = d3.svg.line()
        .x(function(value) {
            return xscale(value);
        })
        .y(function(value, index) {
            var value = yvalues[index];
            if (!$.isNumeric(value)) return -100;
            return yscale(value);
        });

    g.append('svg:path')
        .attr('d', line(xvalues))
        .attr('fill', 'none')
        .attr('stroke', d3.rgb(0, 100, 200));
}

function plotFunction(svg, xscale, yscale, xvalues, yvalues) {
    drawCircles(svg.append('g'), xscale, yscale, xvalues, yvalues);
    drawPath(svg.append('g'), xscale, yscale, xvalues, yvalues);
}

function traceMouse(svg, xscale, yscale, xmin, xmax, width, func,
                    variable, output_variable) {
    var g = svg.append('g');
    var circle = g.append('svg:circle')
        .attr('r', 5)
        .attr('fill', d3.rgb(200, 50, 50))
        .attr('cx', -1000);

    var text = svg.append('g').append('text');
    text.attr('fill', d3.rgb(0, 100, 200));
    text.attr('stroke', 'none');

    var format = d3.format(".4r");

    $(svg[0][0]).mousemove(function(e) {
        var xval = ((e.offsetX - (width / 2)) / width) * (xmax - xmin);
        var yval = func(xval);
        if ($.isNumeric(yval)) {
            circle.attr('cx', xscale(xval));
            circle.attr('cy', yscale(yval));

            text.text(variable + ": " + format(xval) + ", " +
                      output_variable + ": " + format(yval));
            var bbox = text[0][0].getBBox();
            text.attr('x', width / 2 - (bbox.width / 2));
            text.attr('y', bbox.height);
        }
        else {
            circle.attr('cy', -1000);

            text.text("x: " + format(xval));
            var bbox = text[0][0].getBBox();
            text.attr('x', width / 2 - (bbox.width / 2));
            text.attr('y', bbox.height);
        }
    });
}

function setupGraphs() {
    $('.graph').each(function(){
        var WIDTH = 400;
        var HEIGHT = 275;
        var OFFSET_Y = 25;
        var MARGIN_TOP = 25;

        var equation = $(this).data('function').trim();
        var variable = $(this).data('variable');
        var output_variable = 'y';
        if (variable == 'y') {
            output_variable = 'x';
        }
        var f = new Function(variable, 'return ' + equation + ';');

        var xvalues = $(this).data('xvalues');
        var xmin = d3.min(xvalues);
        var xmax = d3.max(xvalues);
        var dx = Math.PI / 16;

        var yvalues = $(this).data('yvalues');
        var ymin = d3.min(yvalues);
        var ymax = d3.max(yvalues);

        if (Math.abs(ymin) >= Math.abs(ymax)) {
            ymax = -ymin;
        }
        else {
            ymin = -ymax;
        }

        var x = d3.scale.linear()
            .domain([xmin, xmax])
            .range([10, WIDTH - 10]);

        var y = d3.scale.linear()
            .domain([Math.ceil(ymax), Math.floor(ymin)])
            .range([OFFSET_Y + MARGIN_TOP, HEIGHT - OFFSET_Y]);

        var graph = d3.select($(this).parent()[0]);
        var svg = graph.append('svg').
            attr('width', WIDTH + 'px').
            attr('height', HEIGHT + 'px');

        // TODO refactor this into a 'Plot' object akin to SymPy's plot
        // object
        drawAxis(x, svg.append('g'), 0,
                 MARGIN_TOP + ((HEIGHT - OFFSET_Y) / 2),
                 'bottom');
        drawAxis(y, svg.append('g'), WIDTH / 2, 0, 'right');
        plotFunction(svg, x, y, xvalues, yvalues);

        traceMouse(svg, x, y, xmin, xmax, WIDTH, f, variable, output_variable);

        // http://stackoverflow.com/questions/2483919
        $(svg[0][0]).attr({
            version: '1.1',
            xmlns: "http://www.w3.org/2000/svg"
        });

        // https://developer.mozilla.org/en-US/docs/DOM/window.btoa
        // supported in everything except IE < 10
        var serializer = new XMLSerializer();
        var svgData = window.btoa(serializer.serializeToString(svg[0][0]));

        var moreButton = $('<button>More...</button>')
            .addClass('card_options_toggle');
        var moreContent = $('<div/>').addClass('card_options');
        moreContent.append([
            $('<div/>').append([
                $('<h2>Export</h2>'),
                $('<a href-lang="image/svg+xml">SVG</a>').attr(
                    'href',
                    'data:image/svg+xml;base64,\n' + svgData
                )
            ])
        ]);
        moreContent.hide();
        moreButton.click(function() {
            moreContent.slideToggle();
        });
        $(this).parents('.result_card').append(moreButton).append(moreContent);
    });
}

$(document).ready(function() {
    $('.cell_output:not(:has(script))').css('opacity', 1);
    MathJax.Hub.Register.MessageHook("New Math", function (message) {
        var script = MathJax.Hub.getJaxFor(message[1]).SourceElement();
        $(script).parent().animate({
            opacity: 1
        }, 700);
    });

    setupGraphs();
});

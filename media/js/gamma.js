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

// http://www.quirksmode.org/js/cookies.html
// Used under terms at http://www.quirksmode.org/about/copyright.html
function createCookie(name,value,days) {
	if (days) {
		var date = new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
	}
	else var expires = "";
	document.cookie = name+"="+value+expires+"; path=/";
}

function readCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}

function eraseCookie(name) {
	createCookie(name,"",-1);
}

var Plot2D = (function() {
    function Plot2D(func, svg, width, height) {
        this._svg = svg;
        this._func = func;
        this._width = width;
        this._height = height;

        this._axesGroup = svg.append('g');
        this._plotGroup = svg.append('g');

        this._xScale = null;
        this._xTicks = 10;
        this._xTickSize = 2;
        this._xGroup = this._axesGroup.append('g');

        this._yScale = null;
        this._yTicks = 10;
        this._yTickSize = 2;
        this._yGroup = this._axesGroup.append('g');

        this._pointGroup = this._plotGroup.append('g');
        this._pathGroup = this._plotGroup.append('g');
        this._xValues = [0.0];
        this._yValues = [0.0];

        this._plotOptions = {
            'grid': true,
            'axes': true
        };
    }

    var makeAxis = function(scale, orientation, ticks, tickSize) {
        return d3.svg.axis()
            .scale(scale)
            .orient(orientation)
            .ticks(ticks)
            .tickSize(tickSize);
    };

    Plot2D.prototype.drawOption = function(options) {
        for (var option in options) {
            if (options.hasOwnProperty(option)) {
                this._plotOptions[option] = options[option]
            }
        }
    };

    Plot2D.prototype.isOptionEnabled = function(option) {
        var opt = this._plotOptions[option];
        return (!(typeof opt === 'undefined')) && opt;
    };

    Plot2D.prototype.xScale = function(xScale) {
        if (xScale == null) {
            return this._xScale;
        }

        this._xScale = xScale;
        this._xAxis = makeAxis(xScale, 'bottom', this._xTicks, this._xTickSize);
    };

    Plot2D.prototype.yScale = function(yScale) {
        if (yScale == null) {
            return this._yScale;
        }

        this._yScale = yScale;
        this._yAxis = makeAxis(yScale, 'right', this._yTicks, this._yTickSize);
    };

    Plot2D.prototype.xValues = function(xValues) {
        this._xValues = xValues;
        this._xMin = d3.min(xValues);
        this._xMax = d3.max(xValues);
    };

    Plot2D.prototype.yValues = function(yValues) {
        this._yValues = yValues;
        this._yMin = d3.min(yValues);
        this._yMax = d3.max(yValues);
    };

    Plot2D.prototype.drawAxes = function() {
        this._axesGroup.selectAll('line').remove();
        this._xGroup.selectAll('*').remove();
        this._yGroup.selectAll('*').remove();

        if (this.isOptionEnabled('axes')) {
            this._xGroup.call(this._xAxis);
            this._xGroup.attr('transform',
                              'translate(' + 0 + ',' + this._yScale(0) + ')');
            this._yGroup.call(this._yAxis);
            this._yGroup.attr('transform',
                              'translate(' + this._width / 2 + ',' + 0 + ')');


            var color = d3.rgb(50,50,50);
            var strokeWidth = 0.5;
            this._axesGroup.selectAll("text")
                .attr("stroke", color)
                .attr("stroke-width", strokeWidth)
                .attr("font-size", 10);
            this._axesGroup.selectAll("path")
                .attr('fill', color)
                .attr('stroke-width', strokeWidth)
                .attr('stroke', 'none');
        }

        if (this.isOptionEnabled('grid')) {
            $.map(this._xScale.ticks(10), $.proxy(function(x) {
                var x = this._xScale(x);
                this._axesGroup.append('svg:line')
                    .attr('x1', x)
                    .attr('y1', this._yScale(this._yMax))
                    .attr('x2', x)
                    .attr('y2', this._yScale(this._yMin))
                    .attr('fill', 'none')
                    .attr('stroke-dasharray', '1, 3')
                    .attr('stroke', d3.rgb(175, 175, 175));
            }, this));

            $.map(this._yScale.ticks(10), $.proxy(function(y) {
                var y = this._yScale(y);
                this._axesGroup.append('svg:line')
                    .attr('x1', this._xScale(this._xMin))
                    .attr('y1', y)
                    .attr('x2', this._xScale(this._xMax))
                    .attr('y2', y)
                    .attr('fill', 'none')
                    .attr('stroke-dasharray', '1, 3')
                    .attr('stroke', d3.rgb(175, 175, 175));
            }, this));
        }
    };

    Plot2D.prototype.drawPoints = function() {
        var points = this._pointGroup.selectAll('circle')
            .data(this._xValues)
            .enter();

        points.append('circle')
            .attr('cx', $.proxy(function(value) {
                return this._xScale(value);
            }, this))
            .attr('cy', $.proxy(function(value, index) {
                return this._yScale(this._yValues[index]);
            }, this))
            .attr('r', 1.5)
            .attr('fill', d3.rgb(0, 100, 200));
    };

    Plot2D.prototype.drawPath = function() {
        var line = d3.svg.line()
            .x($.proxy(function(value) {
                return this._xScale(value);
            }, this))
            .y($.proxy(function(value, index) {
                var value = this._yValues[index];
                return this._yScale(value);
            }, this));

        this._pathGroup.append('svg:path')
            .attr('d', line(this._xValues))
            .attr('fill', 'none')
            .attr('stroke', d3.rgb(0, 100, 200));
    };

    Plot2D.prototype.initTracing = function(variable, output_variable) {
        var traceGroup = this._svg.append('g');
        var tracePoint = traceGroup.append('svg:circle')
            .attr('r', 5)
            .attr('fill', d3.rgb(200, 50, 50))
            .attr('cx', -1000);

        var traceText = traceGroup.append('g').append('text')
            .attr('fill', d3.rgb(0, 100, 200))
            .attr('stroke', 'none');

        var traceXPath = traceGroup.append('svg:line')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', 0)
            .attr('y2', this._height)
            .attr('fill', 'none')
            .attr('stroke-dasharray', '2, 3')
            .attr('stroke', d3.rgb(50, 50, 50));

        var traceYPath = traceGroup.append('svg:line')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', this._width)
            .attr('y2', 0)
            .attr('fill', 'none')
            .attr('stroke-dasharray', '2, 3')
            .attr('stroke', d3.rgb(50, 50, 50));

        var format = d3.format(".4r");

        $(this._svg[0][0]).mousemove($.proxy(function(e) {
            var offsetX = e.offsetX;
            if (typeof e.offsetX == "undefined") {
                offsetX = e.pageX - $(e.target).offset().left;
            }
            var offsetY = e.offsetY;
            if (typeof e.offsetX == "undefined") {
                offsetY = e.pageY - $(e.target).offset().top;
            }
            var xval = (((offsetX - (this._width / 2)) / this._width) *
                        (this._xMax - this._xMin));
            var yval = this._func(xval);

            if ($.isNumeric(yval)) {
                tracePoint.attr('cx', this._xScale(xval));
                tracePoint.attr('cy', this._yScale(yval));

                traceText.text(variable + ": " + format(xval) + ", " +
                          output_variable + ": " + format(yval));
            }
            else {
                tracePoint.attr('cy', -1000);

                traceText.text("x: " + format(xval));
            }

            traceXPath.attr('transform', 'translate(' + this._xScale(xval) + ', 0)');
            traceYPath.attr('transform', 'translate(0, ' + (offsetY) + ')');

            var bbox = traceText[0][0].getBBox();
            traceText.attr('x', this._width / 2 - (bbox.width / 2));
            traceText.attr('y', bbox.height);
        }, this));
    }

    Plot2D.prototype.asSVGDataURI = function() {
        // http://stackoverflow.com/questions/2483919
        var serializer = new XMLSerializer();
        var svgData = window.btoa(serializer.serializeToString(this._svg[0][0]));

        return 'data:image/svg+xml;base64,\n' + svgData;
    }

    // TODO: get PNG data URI (currently not directly possible in Chrome due
    // to security issues)

    return Plot2D;
})();

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

        var ypos = [];
        var yneg = [];
        for (var i = 0; i < yvalues.length; i++) {
            if (yvalues[i] >= 0) {
                ypos.push(yvalues[i]);
            }
            if (yvalues[i] <= 0) {
                yneg.push(yvalues[i]);
            }
        }
        var yposmean = Math.abs(d3.mean(ypos));
        var ynegmean = Math.abs(d3.mean(yneg));

        // Prevent asymptotes from dominating the graph
        if (Math.abs(ymax) >= 10 * yposmean) {
            ymax = yposmean;
        }
        if (Math.abs(ymin) >= 10 * ynegmean) {
            ymin = -ynegmean;
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

        $(svg[0][0]).attr({
            version: '1.1',
            xmlns: "http://www.w3.org/2000/svg"
        });

        var plot = new Plot2D(f, svg, 400, 275);
        plot.xScale(x);
        plot.yScale(y);
        plot.xValues(xvalues);
        plot.yValues(yvalues);

        plot.drawAxes();
        plot.drawPoints();
        plot.drawPath();

        plot.initTracing(variable, output_variable);

        var moreButton = $('<button>More...</button>')
            .addClass('card_options_toggle');
        var moreContent = $('<div/>').addClass('card_options');
        moreContent.append([
            $('<div/>').append([
                $('<h2>Export</h2>'),
                $('<a href-lang="image/svg+xml">SVG</a>').click(function() {
                    $(this).attr(
                        'href',
                        plot.asSVGDataURI()
                    )
                }).attr(
                    'href',
                    plot.asSVGDataURI()
                )
            ]),
            $('<div/>').append([
                $('<h2>Plot Options</h2>'),
                $('<div/>').append([
                    $('<input type="checkbox" checked id="plot-grid" />')
                        .click(function() {
                            plot.drawOption({
                                'grid': $(this).prop('checked')
                            });
                            plot.drawAxes();
                        }),
                    $('<label for="plot-grid">Show Grid</label>'),
                ]),
                $('<div/>').append([
                    $('<input type="checkbox" checked id="plot-axes" />')
                        .click(function() {
                            plot.drawOption({
                                'axes': $(this).prop('checked')
                            });
                            plot.drawAxes();
                        }),
                    $('<label for="plot-axes">Show Axes</label>')
                ])
            ])
        ]);
        moreContent.hide();
        moreButton.click(function() {
            moreContent.slideToggle();
        });
        $(this).parents('.result_card').append(moreButton).append(moreContent);
    });
}

function setupExamples() {
    var delay = 0;
    $('.example-group div.contents').each(function() {
        var contents = $(this);
        var header = $(this).siblings('h3');
        var wasOpen = readCookie(header.html());
        var visitedBefore = readCookie('visitedBefore');

        if (!visitedBefore) {
            createCookie('visitedBefore', true, 365);
        }

        if (!wasOpen || wasOpen === 'false') {
            if (!visitedBefore) {
                contents.delay(500 + delay).slideUp(500);
                delay += 100;
            }
            else {
                contents.hide();
            }
        }
        else {
            header.addClass('shown');
        }
    });

    $('.example-group h3').click(function(e) {
        var header = $(e.target);
        var contents = header.siblings('div.contents');

        contents.stop(false, true).slideToggle(500, function() {
            createCookie(header.html(), contents.is(':visible'), 365);
        });
        header.toggleClass('shown');
    });

    $('#random-example').click(function(e) {
        var examples = $('.example-group a');
        var index = Math.floor(Math.random() * examples.length);
        window.location = $(examples[index]).attr('href');
    });
}

function setupSavedQueries() {
    $('div.col.recent a.remove').click(function(e) {
        var link = $(e.target);
        e.preventDefault();
        link.parent().slideUp(300);
        $.get(link.attr('href'));
    });

    $('#clear-all-recent').click(function() {
        $('div.col.recent a.remove').click();
    })
}

$(document).ready(function() {
    $('.cell_output:not(:has(script))').css('opacity', 1);
    MathJax.Hub.Register.MessageHook("New Math", function (message) {
        var script = MathJax.Hub.getJaxFor(message[1]).SourceElement();
        $(script).parents('.cell_output').animate({
            opacity: 1
        }, 700);
    });

    setupGraphs();

    setupExamples();
    setupSavedQueries();
});

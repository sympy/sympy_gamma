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

var PlotBackend = (function() {
    var makeAxis = function(scale, orientation, ticks, tickSize) {
        return d3.svg.axis()
            .scale(scale)
            .orient(orientation)
            .ticks(ticks)
            .tickSize(tickSize);
    };

    function PlotBackend(plot, container) {
        this.plot = plot;
        this._container = container;

        var graph = d3.select(container);
        this._svg = graph.append('svg')
            .attr('width', plot.width())
            .attr('height', plot.height());

        $(container).find('svg').attr({
            version: '1.1',
            xmlns: "http://www.w3.org/2000/svg"
        });

        this._axesGroup = this._svg.append('g');
        this._plotGroup = this._svg.append('g');

        this._xTicks = 10;
        this._xTickSize = 2;
        this._xAxis = makeAxis(plot.xScale, 'bottom', this._xTicks, this._xTickSize);
        this._xGroup = this._axesGroup.append('g');

        this._yTicks = 10;
        this._yTickSize = 2;
        this._yAxis = makeAxis(plot.yScale, 'right', this._yTicks, this._yTickSize);
        this._yGroup = this._axesGroup.append('g');

        this._pointGroup = this._plotGroup.append('g');
        this._pathGroup = this._plotGroup.append('g');
    }

    PlotBackend.prototype.drawAxes = function() {
        this._axesGroup.selectAll('line').remove();
        this._xGroup.selectAll('*').remove();
        this._yGroup.selectAll('*').remove();

        if (this.plot.isOptionEnabled('axes')) {
            this._xGroup.call(this._xAxis);
            this._xGroup.attr('transform',
                              'translate(' + 0 + ',' + this.plot.yScale(0) + ')');
            this._yGroup.call(this._yAxis);
            this._yGroup.attr('transform',
                              'translate(' + this.plot.width() / 2 + ',' + 0 + ')');


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

        if (this.plot.isOptionEnabled('grid')) {
            var xScale = this.plot.xScale;
            var yScale = this.plot.yScale;

            $.map(xScale.ticks(10), $.proxy(function(x) {
                var x = xScale(x);
                this._axesGroup.append('svg:line')
                    .attr('x1', x)
                    .attr('y1', yScale(this.plot.yMax()))
                    .attr('x2', x)
                    .attr('y2', yScale(this.plot.yMin()))
                    .attr('fill', 'none')
                    .attr('stroke-dasharray', '1, 3')
                    .attr('stroke', d3.rgb(175, 175, 175));
            }, this));

            $.map(yScale.ticks(10), $.proxy(function(y) {
                var y = yScale(y);
                this._axesGroup.append('svg:line')
                    .attr('x1',xScale(this.plot.xMin()))
                    .attr('y1', y)
                    .attr('x2', xScale(this.plot.xMax()))
                    .attr('y2', y)
                    .attr('fill', 'none')
                    .attr('stroke-dasharray', '1, 3')
                    .attr('stroke', d3.rgb(175, 175, 175));
            }, this));
        }
    };

    PlotBackend.prototype.drawPoints = function() {
        var points = this._pointGroup.selectAll('circle')
            .data(this.plot.xValues())
            .enter();

        points.append('circle')
            .attr('cx', $.proxy(function(value) {
                return this.plot.xScale(value);
            }, this))
            .attr('cy', $.proxy(function(value, index) {
                return this.plot.yScale(this.plot.yValues()[index]);
            }, this))
            .attr('r', 1.5)
            .attr('fill', d3.rgb(0, 100, 200));
    };

    PlotBackend.prototype.drawPath = function() {
        var line = d3.svg.line()
            .x($.proxy(function(value) {
                return this.plot.xScale(value);
            }, this))
            .y($.proxy(function(value, index) {
                var value = this.plot.yValues()[index];
                return this.plot.yScale(value);
            }, this));

        this._pathGroup.append('svg:path')
            .attr('d', line(this.plot.xValues()))
            .attr('fill', 'none')
            .attr('stroke', d3.rgb(0, 100, 200));
    };

    PlotBackend.prototype.initTracing = function(variable, output_variable) {
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
            .attr('y2', this.plot.height())
            .attr('fill', 'none')
            .attr('stroke-dasharray', '2, 3')
            .attr('stroke', d3.rgb(50, 50, 50));

        var traceYPath = traceGroup.append('svg:line')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', this.plot.width())
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
            var xval = (((offsetX - (this.plot.width() / 2)) / this.plot.width()) *
                        (this.plot.xMax() - this.plot.xMin()));
            var yval = this.plot.funcValue(xval);

            if ($.isNumeric(yval)) {
                tracePoint.attr('cx', this.plot.xScale(xval));
                tracePoint.attr('cy', this.plot.yScale(yval));

                traceText.text(variable + ": " + format(xval) + ", " +
                          output_variable + ": " + format(yval));
            }
            else {
                tracePoint.attr('cy', -1000);

                traceText.text("x: " + format(xval));
            }

            traceXPath.attr('transform', 'translate(' + this.plot.xScale(xval) + ', 0)');
            traceYPath.attr('transform', 'translate(0, ' + (offsetY) + ')');

            var bbox = traceText[0][0].getBBox();
            traceText.attr('x', this.plot.width() / 2 - (bbox.width / 2));
            traceText.attr('y', bbox.height);
        }, this));
    };

    PlotBackend.prototype.asSVGDataURI = function() {
        // http://stackoverflow.com/questions/2483919
        var serializer = new XMLSerializer();
        var svgData = window.btoa(serializer.serializeToString(this._svg[0][0]));

        return 'data:image/svg+xml;base64,\n' + svgData;
    };

    // TODO: get PNG data URI (currently not directly possible in Chrome due
    // to security issues)

    return PlotBackend;
})();

var Plot2D = (function() {
    function Plot2D(func, xScale, yScale, width, height) {
        this._func = func;
        this._width = width;
        this._height = height;

        this.xScale = xScale;
        this.yScale = yScale;

        this._xValues = [0.0];
        this._yValues = [0.0];

        this._plotOptions = {
            'grid': true,
            'axes': true
        };
    }

    var addGetterSetter = function(func, prop) {
        func.prototype[prop] = function(val) {
            if (val == null) {
                return this['_' + prop];
            }
            this['_' + prop] = val;
        };
    }

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

    addGetterSetter(Plot2D, 'width');
    addGetterSetter(Plot2D, 'height');
    addGetterSetter(Plot2D, 'backend');
    addGetterSetter(Plot2D, 'xMin');
    addGetterSetter(Plot2D, 'xMax');
    addGetterSetter(Plot2D, 'yMin');
    addGetterSetter(Plot2D, 'yMax');

    Plot2D.prototype.funcValue = function(x) {
        return this._func(x);
    }

    Plot2D.prototype.xValues = function(xValues) {
        if (xValues == null) {
            return this._xValues;
        }
        this._xValues = xValues;
        this._xMin = d3.min(xValues);
        this._xMax = d3.max(xValues);
    };

    Plot2D.prototype.yValues = function(yValues) {
        if (yValues == null) {
            return this._yValues;
        }
        this._yValues = yValues;
        this._yMin = d3.min(yValues);
        this._yMax = d3.max(yValues);
    };

    Plot2D.prototype.draw = function() {
        this.backend().drawAxes();
        this.backend().drawPoints();
        this.backend().drawPath();
    };

    Plot2D.prototype.initTracing = function(variable, output_variable) {
        this.backend().initTracing(variable, output_variable)
    };

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

        var plot = new Plot2D(f, x, y, 400, 275);
        plot.xValues(xvalues);
        plot.yValues(yvalues);

        var backend = new PlotBackend(plot, $(this).parent()[0]);
        plot.backend(backend);

        plot.draw();
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
                        plot.backend().asSVGDataURI()
                    )
                }).attr(
                    'href',
                    plot.backend().asSVGDataURI()
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
                            plot.draw();
                        }),
                    $('<label for="plot-grid">Show Grid</label>'),
                ]),
                $('<div/>').append([
                    $('<input type="checkbox" checked id="plot-axes" />')
                        .click(function() {
                            plot.drawOption({
                                'axes': $(this).prop('checked')
                            });
                            plot.draw();
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

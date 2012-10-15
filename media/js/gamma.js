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

var __extend = function(parent, child) {
    for (var key in parent) {
        if (Object.hasOwnProperty.call(parent, key)) {
            child[key] = parent[key];
        }
    }

    function ctor() {
        this.constructor = child;
    }

    ctor.prototype = parent.prototype;
    child.prototype = new ctor();
    child.__super__ = parent.prototype;

    return child;
}

var PlotBackend = (function() {
    function PlotBackend(plot, container) {
        this.plot = plot;
        this._container = container;
    }

    PlotBackend.prototype.clear = function() {
    };

    PlotBackend.prototype.drawAxes = function() {
    };

    PlotBackend.prototype.drawPoints = function() {
    };

    PlotBackend.prototype.drawPath = function() {
    };

    PlotBackend.prototype.initTracing = function(variable, output_variable) {
    };

    return PlotBackend;
})();

var SVGBackend = (function(_parent) {
    __extend(_parent, SVGBackend);

    var makeAxis = function(scale, orientation, ticks, tickSize) {
        return d3.svg.axis()
            .scale(scale)
            .orient(orientation)
            .ticks(ticks)
            .tickSize(tickSize);
    };

    function SVGBackend(plot, container) {
        SVGBackend.__super__.constructor.call(this, plot, container);

        var graph = d3.select(container);
        this._svg = graph.append('svg')
            .attr('width', plot.width())
            .attr('height', plot.height());

        $(container).find('svg').attr({
            version: '1.1',
            xmlns: "http://www.w3.org/2000/svg"
        }).css('resize', 'both');

        this._axesGroup = this._svg.append('g');
        this._plotGroup = this._svg.append('g');

        this._xTicks = 10;
        this._xTickSize = 2;
        this._xGroup = this._axesGroup.append('g');

        this._yTicks = 10;
        this._yTickSize = 2;
        this._yGroup = this._axesGroup.append('g');

        this.generateAxes();

        this._pointGroup = this._plotGroup.append('g');
        this._pathGroup = this._plotGroup.append('g');
    }

    SVGBackend.prototype.generateAxes = function() {
        this._xAxis = makeAxis(this.plot.xScale, 'bottom',
                               this._xTicks, this._xTickSize);
        this._yAxis = makeAxis(this.plot.yScale, 'right',
                               this._yTicks, this._yTickSize);
    };

    SVGBackend.prototype.resize = function() {
        this._svg
            .attr('width', this.plot.width())
            .attr('height', this.plot.height());
    };

    SVGBackend.prototype.clear = function() {
        this._axesGroup.selectAll('line').remove();
        this._xGroup.selectAll('*').remove();
        this._yGroup.selectAll('*').remove();

        this._pointGroup.selectAll('circle').remove();

        this._pathGroup.selectAll('path').remove();
    };

    SVGBackend.prototype.drawAxes = function() {
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

    SVGBackend.prototype.drawPoints = function() {
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

    SVGBackend.prototype.drawPath = function() {
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

    SVGBackend.prototype.initTracing = function(variable, output_variable) {
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

    SVGBackend.prototype.asDataURI = function() {
        // http://stackoverflow.com/questions/2483919
        var serializer = new XMLSerializer();
        var svgData = window.btoa(serializer.serializeToString(this._svg[0][0]));

        return 'data:image/svg+xml;base64,\n' + svgData;
    };

    return SVGBackend;
})(PlotBackend);

var Plot2D = (function() {
    function Plot2D(func, xValues, yValues, width, height) {
        this._func = func;
        this._width = width;
        this._height = height;

        this._xValues = xValues;
        this._xMin = d3.min(xValues);
        this._xMax = d3.max(xValues);
        this._yValues = yValues;
        this._yMin = d3.min(yValues);
        this._yMax = d3.max(yValues);

        this.generateScales();

        this._plotOptions = {
            'grid': true,
            'axes': true,
            'points': true,
            'path': true
        };

        for (var opt in this._plotOptions) {
            var cookie = readCookie(opt);

            if (cookie === 'true') {
                this._plotOptions[opt] = true;
            }
            else if (cookie === 'false') {
                this._plotOptions[opt] = false;
            }
        }
    }

    var addGetterSetter = function(func, prop) {
        func.prototype[prop] = function(val) {
            if (val == null) {
                return this['_' + prop];
            }
            this['_' + prop] = val;
        };
    };

    addGetterSetter(Plot2D, 'width');
    addGetterSetter(Plot2D, 'height');
    addGetterSetter(Plot2D, 'backend');
    addGetterSetter(Plot2D, 'xValues');
    addGetterSetter(Plot2D, 'yValues');
    addGetterSetter(Plot2D, 'xMin');
    addGetterSetter(Plot2D, 'xMax');
    addGetterSetter(Plot2D, 'yMin');
    addGetterSetter(Plot2D, 'yMax');

    Plot2D.prototype.resize = function(width, height) {
        this.width(width);
        this.height(height);
        this.backend().resize();
    };

    Plot2D.prototype.generateScales = function() {
        var OFFSET_Y = 25;
        var MARGIN_TOP = 25;
        this.xScale = d3.scale.linear()
            .domain([this._xMin, this._xMax])
            .range([10, this.width() - 10]);

        var ymin = this.yMin(), ymax = this.yMax();
        var yValues = this.yValues();
        var ypos = [];
        var yneg = [];

        for (var i = 0; i < yValues.length; i++) {
            if (yValues[i] >= 0) {
                ypos.push(yValues[i]);
            }
            if (yValues[i] <= 0) {
                yneg.push(yValues[i]);
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

        this.yScale = d3.scale.linear()
            .domain([Math.ceil(ymax), Math.floor(ymin)])
            .range([OFFSET_Y + MARGIN_TOP, this.height() - OFFSET_Y]);
    };

    Plot2D.prototype.drawOption = function(options) {
        for (var option in options) {
            if (options.hasOwnProperty(option)) {
                this._plotOptions[option] = options[option];

                createCookie(option, options[option], 365);
            }
        }
    };

    Plot2D.prototype.isOptionEnabled = function(option) {
        var opt = this._plotOptions[option];
        return (!(typeof opt === 'undefined')) && opt;
    };

    Plot2D.prototype.funcValue = function(x) {
        return this._func(x);
    };

    Plot2D.prototype.draw = function() {
        this.backend().clear();

        this.backend().drawAxes();
        if (this.isOptionEnabled('points')) {
            this.backend().drawPoints();
        }
        if (this.isOptionEnabled('path')) {
            this.backend().drawPath();
        }
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

        var equation = $(this).data('function').trim();
        var variable = $(this).data('variable');
        var output_variable = 'y';
        if (variable == 'y') {
            output_variable = 'x';
        }
        var f = new Function(variable, 'return ' + equation + ';');

        var xvalues = $(this).data('xvalues');
        var yvalues = $(this).data('yvalues');

        var plot = new Plot2D(f, xvalues, yvalues, WIDTH, HEIGHT);

        var backend = new SVGBackend(plot, $(this)[0]);
        plot.backend(backend);

        var resizing = false;
        var container = $(this);
        var originalWidth = $(this).width();
        var originalHeight = $(this).height();
        $(this).mousedown(function(e) {
            var offsetX = e.offsetX;
            if (typeof e.offsetX == "undefined") {
                offsetX = e.pageX - $(e.target).offset().left;
            }
            var offsetY = e.offsetY;
            if (typeof e.offsetX == "undefined") {
                offsetY = e.pageY - $(e.target).offset().top;
            }
            if (offsetX < 10 ||
                offsetX > container.width() - 10 ||
                offsetY < 10 ||
                offsetY > container.height() - 10) {
                e.preventDefault();
                resizing = true;
            }
        });
        $(document.body).mousemove(function(e) {
            if (resizing) {
                var offset = container.offset();
                var width = container.width();
                var height = container.height();
                var newW = originalWidth;
                var newH = originalHeight;

                // 30 is a fuzz factor to stop the width from "shaking" when
                // the mouse is near the border
                if (e.pageX < offset.left + 30) {
                    newW = width + offset.left - e.pageX;
                }
                else if (e.pageX > (offset.left + width - 30)) {
                    newW = e.pageX - offset.left;
                }

                if (newW < originalWidth) {
                    newW = originalWidth;
                }
                container.width(newW);

                if (e.pageY < offset.top + 30) {
                    newH = originalHeight + offset.top - e.pageY;
                }
                else if (e.pageY > (offset.top + height - 30)) {
                    newH = e.pageY - offset.top;
                }

                if (newH < originalHeight) {
                    newH = originalHeight;
                }
                container.height(newH);

                plot.resize(newW, newH);
                plot.generateScales();
                backend.generateAxes();
                plot.draw();
            }
        });
        $(document.body).mouseup(function() {
            resizing = false;
        });

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
                        plot.backend().asDataURI()
                    )
                }).attr(
                    'href',
                    plot.backend().asDataURI()
                )
            ]),
            $('<div/>').append([
                $('<h2>Plot Options</h2>'),
                $('<div/>').append([
                    $('<input type="checkbox" id="plot-grid" />')
                        .click(function() {
                            plot.drawOption({
                                'grid': $(this).prop('checked')
                            });
                            plot.draw();
                        })
                        .prop('checked', plot.isOptionEnabled('grid')),
                    $('<label for="plot-grid">Show Grid</label>'),
                ]),
                $('<div/>').append([
                    $('<input type="checkbox" checked id="plot-axes" />')
                        .click(function() {
                            plot.drawOption({
                                'axes': $(this).prop('checked')
                            });
                            plot.draw();
                        })
                        .prop('checked', plot.isOptionEnabled('axes')),
                    $('<label for="plot-axes">Show Axes</label>')
                ]),
                $('<div/>').append([
                    $('<input type="checkbox" checked id="plot-points" />')
                        .click(function() {
                            plot.drawOption({
                                'points': $(this).prop('checked')
                            });
                            plot.draw();
                        })
                        .prop('checked', plot.isOptionEnabled('points')),
                    $('<label for="plot-axes">Show Points</label>')
                ]),
                $('<div/>').append([
                    $('<input type="checkbox" checked id="plot-line" />')
                        .click(function() {
                            plot.drawOption({
                                'path': $(this).prop('checked')
                            });
                            plot.draw();
                        })
                        .prop('checked', plot.isOptionEnabled('path')),
                    $('<label for="plot-line">Show Line</label>')
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

function setupMobileKeyboard() {
    var keyboard = $('<div id="mobile-keyboard"/>');

    keyboard.append([
        $('<button data-key="+">+</button>'),
        $('<button data-key="-">-</button>'),
        $('<button data-key="*">*</button>'),
        $('<button data-key="/">/</button>'),
        $('<button data-key="()">()</button>'),
        $('<button data-offset="-1">&lt;</button>'),
        $('<button data-offset="1">&gt;</button>')
    ]);

    var h1height = $('.input h1').height();

    $('.input').prepend(keyboard);
    $('form input[type=text]').focus(function() {
        keyboard.find('button').height(h1height);
        keyboard.slideDown();
        $('.input h1').slideUp();
    });
    $('form input[type=text]').blur(function() {
        setTimeout(function() {
            if (!(document.activeElement.tagName.toLowerCase() == 'input' &&
                  document.activeElement.getAttribute('type') == 'text')) {
                keyboard.slideUp();
                $('.input h1').slideDown();
            }
        }, 100);
    });

    $('#mobile-keyboard button').click(function(e) {
        $('#mobile-keyboard').stop().show().height(h1height);
        $('.input h1').stop().hide();

        var input = $('.input input[type=text]')[0];
        var start = input.selectionStart;
        if ($(this).data('key')) {
            var text = input.value;

            input.value = (text.substring(0, start) +
                           $(this).data('key') + text.substring(start));
            input.setSelectionRange(start + 1, start + 1);
        }
        else if ($(this).data('offset')) {
            var offset = parseInt($(this).data('offset'), 10);
            input.setSelectionRange(start + offset, start + offset);
        }
    });
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

    if (screen.width <= 640) {
        setupMobileKeyboard();
    }
});

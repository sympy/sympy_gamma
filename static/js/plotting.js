var PlotBackend = (function() {
    function PlotBackend(plot, container) {
        this.plot = plot;
        this.plot.backend = this;
        this._container = container;
    }

    PlotBackend.prototype.generateAxes = function() {
    };

    PlotBackend.prototype.resize = function() {
    };

    PlotBackend.prototype.drawAxes = function() {
    };

    PlotBackend.prototype.drawPoints = function() {
    };

    PlotBackend.prototype.drawPath = function() {
    };

    PlotBackend.prototype.draw = function() {
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

        this._gridX = this._axesGroup.selectAll('.x-grid')
            .data(this.plot.xScale.ticks(10));
        this._gridY = this._axesGroup.selectAll('.y-grid')
            .data(this.plot.yScale.ticks(10));
        this._gridX.enter().append('line');
        this._gridY.enter().append('line');

        this._xTicks = 10;
        this._xTickSize = 2;
        this._xGroup = this._axesGroup.append('g');

        this._yTicks = 10;
        this._yTickSize = 2;
        this._yGroup = this._axesGroup.append('g');

        this.generateAxes();

        this._pointGroup = this._plotGroup.append('g');
        this._points = this._pointGroup.selectAll('circle')
            .data(this.plot.xValues());
        this._points.enter().append('circle');

        this._pathGroup = this._plotGroup.append('g');
        this._line = d3.svg.line()
            .x($.proxy(function(value) {
                return this.plot.xScale(value);
            }, this))
            .y($.proxy(function(value, index) {
                var value = this.plot.yValues()[index];
                return this.plot.yScale(value);
            }, this));
        this._path = this._pathGroup.append('svg:path');


        this._traceGroup = this._svg.append('g');
        this._tracePoint = this._traceGroup.append('svg:circle')
            .attr('r', 5)
            .attr('fill', d3.rgb(200, 50, 50))
            .attr('cx', -1000);

        this._traceText = this._traceGroup.append('g').append('text')
            .attr('fill', d3.rgb(0, 100, 200))
            .attr('stroke', 'none');

        this._traceXPath = this._traceGroup.append('svg:line')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', 0)
            .attr('y2', this.plot.height())
            .attr('fill', 'none')
            .attr('stroke-dasharray', '2, 3')
            .attr('stroke', d3.rgb(50, 50, 50));

        this._traceYPath = this._traceGroup.append('svg:line')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', this.plot.width())
            .attr('y2', 0)
            .attr('fill', 'none')
            .attr('stroke-dasharray', '2, 3')
            .attr('stroke', d3.rgb(50, 50, 50));
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
        this._traceXPath.attr('y2', this.plot.height());
        this._traceYPath.attr('x2', this.plot.width());
    };

    SVGBackend.prototype.drawAxes = function() {
        if (this.plot.isOptionEnabled('axes')) {
            this._xGroup.attr('opacity', 1);
            this._yGroup.attr('opacity', 1);

            var yPos = this.plot.yScale(0);
            if (yPos > this.plot.height() - 30) {
                yPos = this.plot.height() - 30;
            }
            else if (yPos < 40) {
                yPos = 40;
            }
            this._xGroup.call(this._xAxis);
            this._xGroup.attr('transform',
                              'translate(' + 0 + ',' + yPos + ')');

            var xPos = this.plot.xScale(0);
            if (xPos > this.plot.width() - 30) {
                xPos = this.plot.width() - 30;
            }
            else if (xPos < 0) {
                xPos = 0;
            }
            this._yGroup.call(this._yAxis);
            this._yGroup.attr('transform',
                              'translate(' + xPos + ',' + 0 + ')');


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
        else {
            this._xGroup.attr('opacity', 0);
            this._yGroup.attr('opacity', 0);
        }

        if (this.plot.isOptionEnabled('grid')) {
            this._gridX.attr('opacity', 1);
            this._gridY.attr('opacity', 1);

            this._gridX.data(this.plot.xScale.ticks(10));
            this._gridY.data(this.plot.yScale.ticks(10));

            var xScale = this.plot.xScale;
            var yScale = this.plot.yScale;

            this._gridX
                .attr('x1', xScale)
                .attr('y1', yScale(this.plot.yTop()))
                .attr('x2', xScale)
                .attr('y2', yScale(this.plot.yBottom()))
                .attr('fill', 'none')
                .attr('stroke-dasharray', '1, 3')
                .attr('stroke', d3.rgb(125, 125, 125));

            this._gridY
                .attr('x1', xScale(this.plot.xLeft()))
                .attr('y1', yScale)
                .attr('x2', xScale(this.plot.xRight()))
                .attr('y2', yScale)
                .attr('fill', 'none')
                .attr('stroke-dasharray', '1, 3')
                .attr('stroke', d3.rgb(125, 125, 125));
        }
        else {
            this._gridX.attr('opacity', 0);
            this._gridY.attr('opacity', 0);
        }
    };

    SVGBackend.prototype.drawPoints = function() {
        if (this.plot.isOptionEnabled('points')) {
            this._points = this._pointGroup.selectAll('circle')
                .data(this.plot.xValues())
                .attr('opacity', 1)
                .attr('cx', $.proxy(function(value) {
                    return this.plot.xScale(value);
                }, this))
                .attr('cy', $.proxy(function(value, index) {
                    return this.plot.yScale(this.plot.yValues()[index]);
                }, this))
                .attr('r', 1.5)
                .attr('fill', d3.rgb(0, 100, 200));
            this._points.enter().append('circle')
        }
        else {
            this._points.attr('opacity', 0);
        }
    };

    SVGBackend.prototype.drawPath = function() {
        if (this.plot.isOptionEnabled('path')) {
            this._path
                .attr('opacity', 1)
                .attr('d', this._line(this.plot.xValues()))
                .attr('fill', 'none')
                .attr('stroke', d3.rgb(0, 100, 200));
        }
        else {
            this._path.attr('opacity', 0);
        }
    };

    SVGBackend.prototype.initTracing = function(variable, output_variable) {
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
                        (this.plot.xRight() - this.plot.xLeft()));
            xval += (this.plot.xRight() + this.plot.xLeft()) / 2;
            var yval = this.plot.funcValue(xval);

            if ($.isNumeric(yval)) {
                this._tracePoint.attr('cx', this.plot.xScale(xval));
                this._tracePoint.attr('cy', this.plot.yScale(yval));

                this._traceText.text(variable + ": " + format(xval) + ", " +
                                     output_variable + ": " + format(yval));
            }
            else {
                this._tracePoint.attr('cy', -1000);

                this._traceText.text("x: " + format(xval));
            }

            this._traceXPath.attr(
                'transform',
                'translate(' + this.plot.xScale(xval) + ', 0)'
            );
            this._traceYPath.attr(
                'transform',
                'translate(0, ' + (offsetY) + ')'
            );

            var bbox = this._traceText[0][0].getBBox();
            this._traceText.attr('x', this.plot.width() / 2 - (bbox.width / 2));
            this._traceText.attr('y', bbox.height);
        }, this));
    };

    SVGBackend.prototype.initDraggingZooming = function() {
        var zoom = d3.behavior.zoom();
        zoom.x(this.plot.xScale);
        zoom.y(this.plot.yScale);
        this._zoomScale = 1;
        zoom.on('zoom', $.proxy(function() {
            this.draw();

            // Zoom = reload all data
            if (d3.event.scale != this._zoomScale) {
                this._zoomScale = d3.event.scale;
                this.plot.reloadData();
                return;
            }

            var xValues = this.plot.xValues();
            var yValues = this.plot.yValues();

            var handleDone = $.proxy(function(data) {
                if (typeof data.output == "undefined") {
                    // TODO: handle error
                    return;
                }
                var el = $(data.output);
                var newXValues = el.data('xvalues');
                var newYValues = el.data('yvalues');

                // TODO find better epsilon
                if (Math.abs(newXValues[0] - this.plot.xMax()) < 0.01) {
                    newXValues.shift();
                    newYValues.shift();
                    this.plot.setData(xValues.concat(newXValues),
                                      yValues.concat(newYValues));
                    this.draw();
                }
                else if (Math.abs(
                    newXValues[newXValues.length - 1] - this.plot.xMin()
                ) < 0.01) {
                    newXValues.pop();
                    newYValues.pop();
                    this.plot.setData(newXValues.concat(xValues),
                                      newYValues.concat(yValues));
                    this.draw();
                }
            }, this);

            // TODO: if function available, some sort of interpolation while
            // waiting for results?
            var xWidth = Math.abs(this.plot.xRight() - this.plot.xLeft());
            var newXLeft = this.plot.xMax();
            var newXRight = this.plot.xMin();
            if (this.plot.xLeft() < this.plot.xMin()) {
                this.plot.fetchData(
                    this.plot.xMin() - Math.floor(xWidth / 2),
                    this.plot.xMin()).done(handleDone);
            }
            else if (this.plot.xRight() > this.plot.xMax()) {
                this.plot.fetchData(
                    this.plot.xMax(),
                    this.plot.xMax() + Math.ceil(xWidth / 2)).done(handleDone);
            }
        }, this));

        this._svg.call(zoom);
        this.zoom = zoom;
    };

    SVGBackend.prototype.draw = function() {
        this.drawAxes();
        this.drawPoints();
        this.drawPath();
    };

    SVGBackend.prototype.asDataURI = function() {
        // http://stackoverflow.com/questions/2483919
        var serializer = new XMLSerializer();
        this._traceGroup.attr('opacity', 0);
        var svgData = window.btoa(serializer.serializeToString(this._svg[0][0]));
        this._traceGroup.attr('opacity', 1);

        return 'data:image/svg+xml;base64,\n' + svgData;
    };

    return SVGBackend;
})(PlotBackend);

var Plot2D = (function() {
    function Plot2D(func, card, xValues, yValues, width, height) {
        this._func = func;
        this._card = card;
        this._width = width;
        this._height = height;

        this._xLeft = -10;
        this._xRight = 10;

        this.setData(xValues, yValues);

        this._fetchRequestPending = false;

        this._plotOptions = {
            'grid': true,
            'axes': true,
            'points': false,
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

        this.generateScales();
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
    addGetterSetter(Plot2D, 'card');
    addGetterSetter(Plot2D, 'xValues');
    addGetterSetter(Plot2D, 'yValues');
    addGetterSetter(Plot2D, 'xMin');
    addGetterSetter(Plot2D, 'xMax');
    addGetterSetter(Plot2D, 'yMin');
    addGetterSetter(Plot2D, 'yMax');

    // TODO setters don't seem to work properly
    Plot2D.prototype.xLeft = function(value) {
        if (typeof value !== "undefined") {
            this.xScale.domain([value, this.xRight()]);
        }
        return this.xScale.domain()[0];
    };

    Plot2D.prototype.xRight = function(value) {
        if (typeof value !== "undefined") {
            this.xScale.domain([this.xLeft(), value]);
        }
        return this.xScale.domain()[1];
    };

    Plot2D.prototype.yTop = function(value) {
        if (typeof value !== "undefined") {
            this.yScale.domain([value, this.yTop()]);
        }
        return this.yScale.domain()[1];
    };

    Plot2D.prototype.yBottom = function(value) {
        if (typeof value !== "undefined") {
            this.yScale.domain([this.yBottom(), value]);
        }
        return this.yScale.domain()[0];
    };

    Plot2D.prototype.setData = function(xValues, yValues) {
        this._xValues = xValues;
        this._xMin = d3.min(xValues);
        this._xMax = d3.max(xValues);
        this._yValues = yValues;
        this._yMin = d3.min(yValues);
        this._yMax = d3.max(yValues);
    };

    Plot2D.prototype.fetchData = function(xMin, xMax) {
        var card = this.card();

        if (this._fetchRequestPending) {
            // TODO enqueue another request if xmin/max beyond this one
            var result = (new $.Deferred()).reject();
            return result;
        }

        this._fetchRequestPending = true;

        card.parameter('xmin', xMin);
        card.parameter('xmax', xMax);

        return card.evaluate("f", "f").always($.proxy(function() {
            this._fetchRequestPending = false;
        }, this));
    };

    Plot2D.prototype.reloadData = function() {
        this.fetchData(this.xLeft(), this.xRight())
        .done($.proxy(function(data) {
            if (typeof data.output == "undefined") {
                // TODO: handle error
                return;
            }
            var el = $(data.output);
            var newXValues = el.data('xvalues');
            var newYValues = el.data('yvalues');
            this.setData(newXValues, newYValues);
            this.backend.draw();
        }, this));
    };

    var OFFSET_Y = 25;
    var MARGIN_TOP = 25;

    Plot2D.prototype.generateScales = function() {
        this.xScale = d3.scale.linear()
            .domain([-10, 10])
            .range([10, this.width() - 10]);

        var yValues = this.yValues();
        var ybottom = this.yMin(), ytop = this.yMax();
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
        if (Math.abs(ytop) >= 10 * yposmean) {
            ytop = yposmean;
        }
        if (Math.abs(ybottom) >= 10 * ynegmean) {
            ybottom = -ynegmean;
        }

        if (this.isOptionEnabled('square')) {
            ytop = d3.max([Math.abs(ytop), Math.abs(ybottom)]);
            ybottom = -yTop;
        }

        this.yScale = d3.scale.linear()
            .domain([ytop, ybottom])
            .range([OFFSET_Y + MARGIN_TOP, this.height() - OFFSET_Y]);
    };

    Plot2D.prototype.resize = function() {
        this.xScale.range([10, this.width() - 10]);
        this.yScale.range([OFFSET_Y + MARGIN_TOP, this.height() - OFFSET_Y]);
    }

    Plot2D.prototype.drawOption = function(option, value) {
        this._plotOptions[option] = value;
        createCookie(option, value, 365);
    };

    Plot2D.prototype.isOptionEnabled = function(option) {
        var opt = this._plotOptions[option];
        return (!(typeof opt === 'undefined')) && opt;
    };

    Plot2D.prototype.funcValue = function(x) {
        return this._func(x);
    };

    return Plot2D;
})();

function setupGraphs() {
    $('.graph').each(function() {
        var WIDTH = 400;
        var HEIGHT = 275;

        // Make things fit on mobile
        var IS_MOBILE = window.matchMedia("screen and (max-device-width: 1280px)").matches;
        if (IS_MOBILE) {
            WIDTH = $(this).width() - 20;
        }

        var equation = $(this).data('function').trim();
        var variable = $(this).data('variable');
        var output_variable = 'y';
        if (variable == 'y') {
            output_variable = 'x';
        }
        var f = new Function(variable, 'return ' + equation + ';');

        var xvalues = $(this).data('xvalues');
        var yvalues = $(this).data('yvalues');

        var card = $(this).parents('.result_card').data('card');

        var plot = new Plot2D(f, card, xvalues, yvalues, WIDTH, HEIGHT);
        var backend = new SVGBackend(plot, $(this)[0]);

        var resizing = false;
        var container = $(this);
        var originalWidth = $(this).width();
        var originalHeight = $(this).height();
        var originalYTop = plot.yTop();
        var originalYBottom = plot.yBottom();

        if (!IS_MOBILE) {
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
            $(this).mousemove(function(e) {
                var offsetX = e.offsetX;
                if (typeof e.offsetX == "undefined") {
                    offsetX = e.pageX - $(e.target).offset().left;
                }
                var offsetY = e.offsetY;
                if (typeof e.offsetX == "undefined") {
                    offsetY = e.pageY - $(e.target).offset().top;
                }
                var width = container.width();
                var height = container.height();
                if (offsetX < 10) {
                    if (offsetY < 10) {
                        container.css('cursor', 'nw-resize');
                    }
                    else if (height - offsetY < 10) {
                        container.css('cursor', 'sw-resize');
                    }
                    else {
                        container.css('cursor', 'w-resize');
                    }
                }
                else if (width - offsetX < 10) {
                    if (offsetY < 10) {
                        container.css('cursor', 'ne-resize');
                    }
                    else if (height - offsetY < 10) {
                        container.css('cursor', 'se-resize');
                    }
                    else {
                        container.css('cursor', 'e-resize');
                    }
                }
                else if (offsetY < 10) {
                    container.css('cursor', 'n-resize');
                }
                else if (height - offsetY < 10) {
                    container.css('cursor', 's-resize');
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
                    container.css('max-width', newW + 'px');

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

                    plot.width(newW);
                    plot.height(newH);
                    plot.resize();
                    backend.resize();
                    backend.generateAxes();
                    backend.draw();
                }
            });
            $(document.body).mouseup(function() {
                resizing = false;
            });
        }

        backend.draw();
        if (!IS_MOBILE) {
            backend.initTracing(variable, output_variable);
        }
        backend.initDraggingZooming();

        var moreButton = $('<button><i class="icon-angle-down"></i> More...</button>')
            .addClass('card_options_toggle')
            .addClass('card_options_more');
        var moreContent = $('<div/>');

        var options = $.map(['grid', 'axes', 'points', 'path'], function(opt) {
            var opt = opt;
            return $('<div/>').append([
                $('<input type="checkbox" id="plot-' + opt + '" />')
                    .click(function(e) {
                        plot.drawOption(opt, $(e.target).prop('checked'));
                        backend.draw();
                    })
                    .prop('checked', plot.isOptionEnabled(opt)),
                $('<label for="plot-'+ opt + '">Show ' + opt + '</label>'),
            ]);
        });

        moreContent.append([
            $('<div/>').append([
                $('<h2>Export</h2>'),
                $('<a href-lang="image/svg+xml">SVG</a>').click(function() {
                    $(this).attr(
                        'href',
                        backend.asDataURI()
                    )
                }).attr(
                    'href',
                    backend.asDataURI()
                )
            ]),
            $('<div/>').append($('<h2>Plot Options</h2>')).append(options)
        ]);

        moreContent.hide();
        moreButton.click(function() {
            moreContent.slideToggle();
            moreButton.toggleClass('open');
        });
        var options = $(this).parents('.result_card').find('.card_options');
        options.append([
            $('<p>Drag plot to pan, (shift-)double-click to zoom, drag edges to resize</p>')
                .addClass('help'),
            $('<button>Reset</button>')
                .addClass('card_options_toggle')
                .click(function() {
                    container.width(originalWidth);
                    container.height(originalHeight);
                    plot.drawOption('square', false);
                    plot.width(originalWidth);
                    plot.height(originalHeight);
                    backend.resize();
                    plot.resize();
                    plot.xScale.domain([-10, 10]);
                    plot.yScale.domain([originalYBottom, originalYTop]);
                    plot.reloadData();
                    backend.generateAxes();
                    backend.draw();
                    backend.initDraggingZooming();
                }),
            $('<button>Square Viewport</button>')
                .addClass('card_options_toggle')
                .click(function() {
                    var side = d3.max([container.width(), container.height()]);
                    container.width(side);
                    container.height(side);
                    plot.drawOption('square', true);
                    plot.width(side);
                    plot.height(side);

                    var centerX = Math.floor((plot.xRight() + plot.xLeft()) / 2);
                    var centerY = Math.floor((plot.yTop() + plot.yBottom()) / 2);
                    var extent = d3.max([plot.xRight(), plot.xLeft(),
                                         plot.yTop(), plot.yBottom()], Math.abs);
                    plot.xLeft(Math.floor(centerX - extent / 2));
                    plot.xRight(Math.ceil(centerX + extent / 2));
                    plot.yTop(Math.ceil(centerY + extent / 2));
                    plot.yBottom(Math.floor(centerY - extent / 2));
                    backend.resize();
                    plot.resize();
                    backend.generateAxes();
                    backend.draw();
                    backend.initDraggingZooming();
                }),
            $('<button>Fullscreen</button>')
                .addClass('card_options_toggle')
                .click(function() {
                    card.toggleFullscreen();
                }),
            moreButton,
            moreContent
        ]);
    });
}

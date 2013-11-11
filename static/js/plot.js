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
    }

    return PlotBackend;
})();

var D3Backend = (function(_parent) {
    __extend(_parent, D3Backend);

    function D3Backend(plot, container) {
        D3Backend.__super__.constructor.call(this, plot, container);

        this.svg = d3.select(container)
            .append('svg')
            .attr({
                width: plot.width(),
                height: plot.height(),
                version: '1.1',
                xmlns: 'http://www.w3.org/2000/svg'
            });

        // Disable scroll wheel zoom
        // https://developer.mozilla.org/en-US/docs/Web/Reference/Events/wheel
        var wheel_event = (
            ("onwheel" in document.createElement("div")) ?
                "wheel" : (document.onmousewheel !== undefined) ?
                "mousewheel" :
                "DOMMouseScroll");
        this.svg.on(wheel_event, function() {
            d3.event.stopImmediatePropagation();
        });

        this.zoom = d3.behavior.zoom()
            .size([this.plot.width(), this.plot.height()])
            .x(this.plot.scales.x)
            .y(this.plot.scales.y);
        this.zoom.on('zoom', $.proxy(this._handleZoom, this));
        this.svg.call(this.zoom);
        this.graphs = [];
    }

    D3Backend.prototype._handleZoom = function() {
        this.updateAxes();
        this.updateGrid();
        for (var i = 0; i < this.graphs.length; i++) {
            this.graphs[i].update();
        }
        if (d3.event !== null) {
            this.plot.retrieveData({ scale: d3.event.scale });
        }
    };

    D3Backend.prototype.showAxes = function() {
        this.svg.select('.axes').remove();
        this.axes = this.svg.append('g').attr('class', 'axes');
        this.xAxis = d3.svg.axis().scale(this.plot.scales.x).orient('bottom').ticks(10).tickSize(2);
        this.yAxis = d3.svg.axis().scale(this.plot.scales.y).orient('right').ticks(10).tickSize(2);
        this.axes.append('g').attr('class', 'x-axis');
        this.axes.append('g').attr('class', 'y-axis');
        this.updateAxes();
    };

    D3Backend.prototype.hideAxes = function() {
        this.svg.select('.axes').remove();
    };

    D3Backend.prototype.updateAxes = function() {
        this.axes.select('.x-axis').call(this.xAxis);
        this.axes.select('.y-axis').call(this.yAxis);
        var yPos = this.plot.scales.y(0) - 0.5;
        this.xAxis.orient('bottom');
        if (yPos > this.plot.height()) {
            yPos = this.plot.height();
            this.xAxis.orient('top');
        }
        else if (yPos < 0) {
            yPos = 0;
        }
        var xPos = this.plot.scales.x(0) - 0.5;
        this.yAxis.orient('right');
        if (xPos > this.plot.width()) {
            xPos = this.plot.width();
            this.yAxis.orient('left');
        }
        else if (xPos < 0) {
            xPos = 0;
        }
        this.svg.select('.x-axis').attr('transform', 'translate(0,' + yPos + ')');
        this.svg.select('.y-axis').attr('transform', 'translate(' + xPos + ', 0)');
    };

    D3Backend.prototype.showGrid = function() {
        this.svg.select('.grid').remove();
        this.grid = this.svg.append('g').attr('class', 'grid');
        this.xGrid = this.grid.append('g').attr('class', 'x-grid');
        this.yGrid = this.grid.append('g').attr('class', 'y-grid');
        this.updateGrid();
    };

    D3Backend.prototype.hideGrid = function() {
        this.svg.select('.grid').remove();
    };

    D3Backend.prototype.updateGrid = function() {
        var x = this.xGrid.selectAll('line').data(this.plot.scales.x.ticks(10));
        x.enter().append('line');
        x.exit().remove();
        x.attr({
            x1: this.plot.scales.x,
            y1: this.plot.scales.y(this.plot.scales.y.domain()[1]),
            x2: this.plot.scales.x,
            y2: this.plot.scales.y(this.plot.scales.y.domain()[0]),
            fill: 'none',
            stroke: d3.rgb(125, 125, 125)
        }).attr('stroke-dasharray', '1, 3');

        var y = this.yGrid.selectAll('line').data(this.plot.scales.y.ticks(10));
        y.enter().append('line');
        y.exit().remove();
        y.attr({
            x1: this.plot.scales.x(this.plot.scales.x.domain()[0]),
            y1: this.plot.scales.y,
            x2: this.plot.scales.x(this.plot.scales.x.domain()[1]),
            y2: this.plot.scales.y,
            fill: 'none',
            stroke: d3.rgb(125, 125, 125)
        }).attr('stroke-dasharray', '1, 3');
    };

    D3Backend.prototype.showCrosshair = function() {
        this.crosshair = this.svg.append('g').attr('class', 'crosshair');
        this.crosshair.append('line').attr({
            'class': 'x',
            x1: 0,
            y1: 0,
            fill: 'none',
            stroke: d3.rgb(25, 25, 25)
        });
        this.crosshair.append('line').attr({
            'class': 'y',
            x1: 0,
            y1: 0,
            fill: 'none',
            stroke: d3.rgb(25, 25, 25)
        });
        this.updateCrosshair({ x: 0, y: 0 });
    };

    D3Backend.prototype.hideCrosshair = function() {
        this.svg.select('.crosshair').remove();
    };

    D3Backend.prototype.updateCrosshair = function(offset) {
        this.crosshair.select('.x').attr({
            y1: offset.y,
            x2: this.plot.scales.x(this.plot.scales.x.domain()[1]),
            y2: offset.y
        });
        this.crosshair.select('.y').attr({
            x1: offset.x,
            x2: offset.x,
            y2: this.plot.scales.y(this.plot.scales.y.domain()[0])
        });
    };

    D3Backend.prototype.makeGraph = function(graph, color) {
        var points = this.svg.append('g').attr('class', 'points');
        var path = this.svg.append('g').attr('class', 'path').append('svg:path');
        var line = d3.svg.line().x(this.plot.scales.x);

        var updatePoints = $.proxy(function(graph) {
            var circles = points.selectAll('circle')
                .data(graph.points.x);
            circles.exit().remove('circle');
            circles.enter().append('circle');
            points.selectAll('circle')
                .attr({
                    cx: this.plot.scales.x,
                    cy: $.proxy(function(value, index) {
                        return this.plot.scales.y(graph.points.y[index]);
                    }, this),
                    r: 2,
                    fill: color
                });
        }, this);
        var updateLine = $.proxy(function(graph) {
            line.x(this.plot.scales.x)
                .y($.proxy(function(value, index) {
                    return this.plot.scales.y(graph.points.y[index])
                }, this));
            path.attr({
                d: line(graph.points.x),
                fill: 'none',
                stroke: color,
                opacity: 0.8
            }).attr('stroke-width', 1.5);
        }, this);

        var visible = true;
        var highlight = false;
        var g = {
            update: $.proxy(function(_graph) {
                if (typeof _graph !== "undefined") {
                    graph = _graph;
                }
                if (this.plot.option('points')) {
                    updatePoints(graph);
                    points.attr('display', 'block');
                }
                else {
                    points.attr('display', 'none');
                }

                if (this.plot.option('path')) {
                    updateLine(graph);
                    path.attr('display', 'block');
                }
                else {
                    path.attr('display', 'none');
                }
            }, this),

            toggle: function() {
                if (visible) {
                    path.attr('display', 'none');
                    points.attr('display', 'none');
                }
                else {
                    this.update();
                }
                visible = !visible;
            },

            highlight: function() {
                if (!highlight) {
                    path.attr('stroke-width', 3);
                    points.selectAll('circle').attr('r', 3);
                }
                else {
                    path.attr('stroke-width', 1.5);
                    points.selectAll('circle').attr('r', 2);
                }
                highlight = !highlight;
            }
        };
        this.graphs.push(g);
        return g;
    };

    D3Backend.prototype.resize = function(options) {
        this.svg.attr({
            width: this.plot.width(),
            height: this.plot.height()
        });
        if (typeof options !== "undefined" && options.updateZoom) {
            this.zoom
                .size([this.plot.width(), this.plot.height()])
                .x(this.plot.scales.x)
                .y(this.plot.scales.y);
        }
    };

    D3Backend.prototype.reset = function() {
        d3.transition().duration(300).tween("zoom", $.proxy(function() {
            var x = this.plot.scales.x;
            var y = this.plot.scales.y;
            var ix = d3.interpolate(x.domain(), [-10, 10]);
            var iy = d3.interpolate(y.domain(), this.plot.calculateYRange());
            return $.proxy(function(t) {
                this.zoom
                    .x(x.domain(ix(t)))
                    .y(y.domain(iy(t)));
                this._handleZoom();
            }, this);
        }, this));
    };

    D3Backend.prototype.asDataURI = function() {
        // http://stackoverflow.com/questions/2483919
        this.hideCrosshair();
        var serializer = new XMLSerializer();
        var svgData = window.btoa(serializer.serializeToString(this.svg[0][0]));
        this.showCrosshair();
        return 'data:image/svg+xml;base64,\n' + svgData;
    };

    return D3Backend;
})(PlotBackend);

var Plot2D = (function() {
    function Plot2D(card, container, backendClass, graphs) {
        this.card = card;
        this._container = $(container);
        this._graphs = graphs;
        this.graphs = [];
        this.options = {
            grid: true,
            axes: true,
            points: false,
            path: true
        };

        for (var opt in this.options) {
            if (!this.options.hasOwnProperty(opt)) {
                continue;
            }
            var cookie = readCookie(opt);

            if (cookie === 'true') {
                this.options[opt] = true;
            }
            else if (cookie === 'false') {
                this.options[opt] = false;
            }
        }

        this._scale = 1;
        this._requestPending = false;

        this._generateScales();
        this._backend = new backendClass(this, container);
        this._calculateExtent();
    }

    Plot2D.prototype._generateScales = function() {
        if (typeof this.scales === "undefined") {
            this.scales = {
                x: d3.scale.linear(),
                y: d3.scale.linear()
            };
        }
        this.scales.x.domain([-10, 10]).range([10, this.width() - 10]);
        this.scales.y.domain(this.calculateYRange()).range([this.height() - 10, 10]);
    };

    Plot2D.prototype._calculateExtent = function() {
        this._extent = {
            min: d3.min(this._graphs.map(function(g) { return d3.min(g.points.x); })),
            max: d3.max(this._graphs.map(function(g) { return d3.max(g.points.x); }))
        };
    };

    Plot2D.prototype.calculateYRange = function() {
        if (typeof this._originalExtent !== "undefined") {
            return this._originalExtent;
        }

        var ypos = [];
        var yneg = [];
        var ytop = 0;
        var ybottom = 0;
        this._graphs.forEach(function(graph) {
            graph.points.y.forEach(function(y) {
                if (y < ybottom) {
                    ybottom = y;
                }
                else if (y > ytop) {
                    ytop = y;
                }

                if (y <= 0) {
                    yneg.push(y);
                }
                else if (y > 0) {
                    ypos.push(y);
                }
            });
        });

        var yposmean = Math.abs(d3.mean(ypos));
        var ynegmean = Math.abs(d3.mean(yneg));

        // Prevent asymptotes from dominating the graph
        if (Math.abs(ytop) >= 10 * yposmean) {
            ytop = yposmean;
        }
        if (Math.abs(ybottom) >= 10 * ynegmean) {
            ybottom = -ynegmean;
        }
        this._originalExtent = [ybottom, ytop];
        return this._originalExtent;
    };

    Plot2D.prototype.width = function() {
        return Math.round(this._container.width());
    };

    Plot2D.prototype.height = function() {
        return Math.round(this._container.height());
    };

    Plot2D.prototype.show = function() {
        this._backend.showAxes(this.scales);
        this._backend.showGrid(this.scales);

        var colors = d3.scale.category10();
        for (var i = 0; i < this._graphs.length; i++) {
            var graph = this._backend.makeGraph(this._graphs[i], colors(i));
            graph.update();
            this.graphs.push(graph);
        }

        this._backend.showCrosshair();
    };

    Plot2D.prototype.update = function() {
        if (this.option('axes')) {
            this._backend.showAxes(this.scales);
        }
        else {
            this._backend.hideAxes();
        }

        if (this.option('grid')) {
            this._backend.showGrid(this.scales);
        }
        else {
            this._backend.hideGrid();
        }

        for (var i = 0; i < this.graphs.length; i++) {
            var graph = this.graphs[i];
            graph.update();
        }
    };

    Plot2D.prototype.retrieveData = function(view) {
        if (view.scale != this._scale) {
            this._scale = view.scale;
            this.fetch(this.scales.x.domain()[0], this.scales.x.domain()[1], 'replace');
        }
        else {
            var half = (this._extent.max - this._extent.min)/2;
            if (this.scales.x.domain()[0] < this._extent.min) {
                this.fetch(Math.round(this.scales.x.domain()[0] - half), this._extent.min, 'prepend');
            }
            if (this.scales.x.domain()[1] > this._extent.max) {
                this.fetch(this._extent.max, Math.round(this.scales.x.domain()[1] + half), 'append');
            }
        }
    };

    // mode: replace, prepend, or append
    Plot2D.prototype.fetch = function(xMin, xMax, mode) {
        if (!this._requestPending) {
            this.card.parameter('xmin', xMin);
            this.card.parameter('xmax', xMax);
            this._requestPending = true;
            this.card.evaluate($.proxy(function(data) {
                if (typeof data.output == "undefined") {
                    // TODO: handle error
                    return;
                }
                var data = JSON.parse($(data.output).find('.graphs').text());
                if (mode === 'replace') {
                    this._graphs = data;
                }
                else if (mode === 'prepend') {
                    for (var i = 0; i < this.graphs.length; i++) {
                        var graph = this._graphs[i];
                        data[i].points.x.pop();
                        data[i].points.y.pop();
                        graph.points.x = data[i].points.x.concat(graph.points.x);
                        graph.points.y = data[i].points.y.concat(graph.points.y);
                    }
                }
                else if (mode === 'append') {
                    for (var i = 0; i < this.graphs.length; i++) {
                        var graph = this._graphs[i];
                        data[i].points.x.shift();
                        data[i].points.y.shift();
                        graph.points.x = graph.points.x.concat(data[i].points.x);
                        graph.points.y = graph.points.y.concat(data[i].points.y);
                    }
                }

                for (var i = 0; i < this.graphs.length; i++) {
                    this.graphs[i].update(this._graphs[i]);
                }
                this._calculateExtent();
            }, this), function() {
                // TODO: handle errors
            }).always($.proxy(function() {
                this._requestPending = false;
            }, this));
        }
        else {
        }
    };

    Plot2D.prototype.toggle = function(index) {
        this.graphs[index].toggle();
    };

    Plot2D.prototype.highlight = function(index) {
        this.graphs[index].highlight();
    };

    Plot2D.prototype.resize = function(options) {
        this.scales.x.range([10, this.width() - 10]);
        this.scales.y.range([this.height() - 10, 10]);
        this._backend.resize(options);
        this.update();
    };

    Plot2D.prototype.reset = function() {
        this._backend.reset();
        setTimeout($.proxy(function() {
            this.retrieveData({ scale: 1 });
        }, this), 300);
    };

    Plot2D.prototype.option = function(opt, value) {
        if (typeof value === "undefined") {
            return this.options[opt];
        }
        this.options[opt] = value;
        createCookie(opt, value, 365);
    };

    Plot2D.prototype.asDataURI = function() {
        return this._backend.asDataURI();
    }

    return Plot2D;
})();

// Graph object

// {
//     type: 'polar',
//     points: {
//         x: [], // these are the coordinates to actually display
//         y: []
//     },
//     data: {
//         r: [], // shown to user
//         theta: []
//     }
// }

function setupPlots() {
    $('.plot').each(function() {
        var variable = $(this).data('variable');
        var output_variable = 'y';
        if (variable == 'y') {
            output_variable = 'x';
        }
        var card = $(this).parents('.result_card').data('card');
        var graphs = JSON.parse($(this).find('.graphs').text());

        var plot = new Plot2D(card, $(this)[0], D3Backend, graphs);
        plot.show();

        // Highlight the input function with the graph line color
        var colors = d3.scale.category10();
        card.element.addClass('plot-card');
        card.element.find('.cell_input span').each(function(index) {
            var element = $(this)
                .css('color', colors(index))
                .attr('title', 'Click to toggle visibility')
                .hover(function() {
                    plot.highlight(index);
                })
                .click(function() {
                    plot.toggle(index);
                    element.toggleClass('hidden');
                });
        });

        var resizing = false;
        var container = $(this);

        container.find('svg').mousemove(function(e) {
            plot._backend.updateCrosshair({ x: e.offsetX, y: e.offsetY });
        });

        var originalWidth = container.width();
        var originalHeight = container.height();

        card.addOptionsSection();
        var moreButton = $('<button><i class="icon-angle-down"></i> More...</button>')
            .addClass('card_options_toggle')
            .addClass('card_options_more');
        var moreContent = $('<div/>');

        var options = $.map(['grid', 'axes', 'points', 'path'], function(opt) {
            var opt = opt;
            return $('<div/>').append([
                $('<input type="checkbox" id="plot-' + opt + '" />')
                    .click(function(e) {
                        plot.option(opt, $(e.target).prop('checked'));
                        plot.update();
                    })
                    .prop('checked', plot.option(opt)),
                $('<label for="plot-'+ opt + '">Show ' + opt + '</label>'),
            ]);
        });

        moreContent.append([
            $('<div/>').append([
                $('<h2>Export</h2>'),
                $('<a href-lang="image/svg+xml">SVG</a>').click(function() {
                    $(this).attr('href', plot.asDataURI())
                }).attr('href', plot.asDataURI())
            ]),
            $('<div/>').append($('<h2>Plot Options</h2>')).append(options)
        ]);

        moreContent.hide();
        moreButton.click(function() {
            moreContent.slideToggle();
            moreButton.toggleClass('open');
        });
        var options = container.parents('.result_card').find('.card_options');
        var resizeContainer = function(options) {
            var reset = (typeof options.reset === "undefined") ? false : options.reset;

            if (reset) {
                plot.reset();
            }

            container.animate({
                width: options.width,
                height: options.height
            }, {
                duration: 300,
                progress: function() {
                    plot.resize();
                },
                complete: function() {
                    if (reset) {
                        plot.reset();
                    }
                    plot.resize({ updateZoom: true });
                }
            });
        };
        options.append([
            $('<p>Drag to pan, (shift-)double-click to zoom, drag corner to resize</p>')
                .addClass('help'),
            $('<button>Reset</button>')
                .addClass('card_options_toggle')
                .click(function() {
                    plot.reset();
                    resizeContainer({
                        width: originalWidth,
                        height: originalHeight,
                        reset: true
                    });
                }),
            $('<button>Square Viewport</button>')
                .addClass('card_options_toggle')
                .click(function() {
                    var size = d3.max([container.width(), container.height()]);
                    resizeContainer({
                        width: size,
                        height: size
                    });
                }),
            $('<button>Fullscreen</button>')
                .addClass('card_options_toggle')
                .click(function() {
                    card.toggleFullscreen();
                }),
            moreButton,
            moreContent
        ]);

        if (!window.matchMedia("screen and (max-device-width: 1280px)").matches) {
            container.mousemove(function(e) {
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
                if ((width - offsetX < 10) && (height - offsetY < 10)) {
                    container.css('cursor', 'se-resize');
                }
                else {
                    container.css('cursor', 'default');
                }
            });


            var observer = new MutationObserver(function(mutations) {
                if (mutations[0].attributeName === "style") {
                    var width = container.width(), height = container.height();
                    plot.width(width);
                    plot.height(height);
                    plot.resize();
                }
            });
            observer.observe(container.get(0), {
                attributes: true
            });
        }
    });
}

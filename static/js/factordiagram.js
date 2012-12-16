// http://mathlesstraveled.com/2012/10/05/factorization-diagrams/
var FactorDiagram = (function() {
    function FactorDiagram(container, primes) {
        this._container = container;
        this._primes = primes;
        this._svg = container.append('svg');
        this._defs = this._svg.append('svg:defs');
        this._defs.append('circle').
            attr('id', 'c').
            attr('r', 2);
    }

    var translate = function(x, y) {
        return 'translate(' + x + ',' + y + ')';
    };

    FactorDiagram.prototype._dimensions = function(id) {
        var el = this._svg.append('use').attr('xlink:href', id);
        var bbox = el[0][0].getBBox();
        el.remove();
        return bbox;
    };

    FactorDiagram.prototype.primeLayout = function(n, id, g) {
        var dims = this._dimensions(id);
        var w = dims.width;
        var h = dims.height;

        if (n == 1) {
            g.append('svg:g')
                .append('circle')
                .attr('r', 2)
        }
        else if (n == 2) {
            if (w > h) {
                g.append('svg:g')
                    .append('svg:use')
                    .attr('xlink:href', id)
                    .attr('transform', translate(0, -h/2));
                g.append('svg:g').attr('transform', translate(0, h))
                    .append('svg:use')
                    .attr('xlink:href', id);
            }
            else {
                g.append('svg:g')
                    .append('svg:use')
                    .attr('xlink:href', id)
                    .attr('transform', translate(-w/2, 0));
                g.append('svg:g').attr('transform', translate(w, 0))
                    .append('svg:use')
                    .attr('xlink:href', id);
            }
        }
        else {
            for (var i = 0; i < n; i++) {
                var m = d3.max([w, h]);
                m = m * 0.75 / Math.sin((2 * Math.PI) / (2 * n));
                var alpha = i * (2 * Math.PI / n);
                alpha -= Math.PI / 2;
                var x = m * Math.cos(alpha);
                var y = m * Math.sin(alpha);
                g.append('svg:g')
                    .append('svg:use')
                    .attr('xlink:href', id)
                    .attr('transform', translate(x, y));
            }
        }
    };

    FactorDiagram.prototype.draw = function() {
        var factorDiagram = function(primes, num) {
            if (primes.length === 0) {
                return '#c';
            }
            else {
                var p = primes[0];
                var rest = primes.slice(1);
                var g = this._defs.append('svg:g').attr('id', 'g' + num);
                var next = factorDiagram.call(this, rest, num + 1);
                this.primeLayout(p, next, g, 2, 2);
                return '#' + g.attr('id');
            }
        };
        var diagram = factorDiagram.call(this, this._primes, 0);
        var el = this._svg.append('svg:use')
            .attr('xlink:href', diagram)
            .attr('id', 'diagram');
        var d = this._dimensions('#diagram');
        el.attr('transform', translate(-d.x, -d.y));
        this._svg.attr('width', d.width);
        this._svg.attr('height', d.height);
    };

    return FactorDiagram;
})();

function setupFactorization() {
    $('div.factorization-diagram').each(function() {
        var primes = $(this).data('primes');
        var f = new FactorDiagram(d3.select($(this).children('div')[0]), primes);
        f.draw();
    });
}

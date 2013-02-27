var Card = (function() {
    function Card(card_el) {
        this.card = card_el;
        this.output = card_el.find('.cell_output');
        this.card_name = this.output.data('card-name');

        if (typeof this.card_name === "undefined") {
            return;
        }

        this.result = $("<div/>");
        this.output.append(this.result);
        this.variable = encodeURIComponent(this.output.data('variable'));
        this.expr = encodeURIComponent(this.output.data('expr'));
        this.parameters = this.output.data('parameters');
        this.parameterValues = {};

        if (this.parameters.indexOf('digits') !== -1) {
            var moreDigits = $('<a href="#">More digits…</a>');
            this.parameter('digits', 15);
            this.output.parent().append(
                $("<div/>").addClass('card_options').append(
                    $('<button/>').append(moreDigits).addClass('card_options_toggle')
                )
            );
            moreDigits.click($.proxy(function() {
                var delta = 10;
                if (this.parameter('digits') <= 15) {
                    delta = 35;
                }
                this.parameter('digits', this.parameter('digits') + delta);
                this.evaluate();
            }, this));
        }
    }

    Card.prototype.parameter = function(key, val) {
        if (val != null) {
            this.parameterValues[key] = val;
        }
        return this.parameterValues[key];
    };

    // TODO use Deferred to replace parameters
    Card.prototype.evaluate = function(finished, error) {
        if (finished == null) {
            finished = $.proxy(this.evaluateFinished, this);
        }
        if (error == null) {
            error = $.proxy(this.evaluateError, this);
        }
        if (typeof this.card_name !== "undefined") {
            var url = '/card/' + this.card_name;
            var parms = {
                variable: this.variable,
                expression: this.expr
            };
            $.extend(parms, this.parameterValues);
            var deferred = $.getJSON(url, parms, finished);
            deferred.error(error);
            return deferred;
        }
        var result = new $.Deferred();
        result.reject();
        return result;
    };

    Card.prototype.evaluateFinished = function(data) {
        if (typeof data.output !== "undefined") {
            this.result.html(data.output);

            MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
        }
        else {
            var error = $("<div/>")
                .addClass('cell_output_plain')
                .html(data.error);
            this.output.append(error);
            this.card.addClass('result_card_error');
        }
        this.output.children('.loader').fadeOut(500);
    };

    Card.prototype.evaluateError = function() {
        this.output.append($("<div/>").html("Error occurred"));
        this.output.children('.loader').fadeOut(500);
    };

    return Card;
})();

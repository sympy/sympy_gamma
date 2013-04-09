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
            this.addOptionsSection();
            var moreDigits = this.addOptionsButton('More Digits');

            this.parameter('digits', 15);
            moreDigits.click($.proxy(function() {
                var delta = 10;
                if (this.parameter('digits') <= 15) {
                    delta = 35;
                }
                this.parameter('digits', this.parameter('digits') + delta);
                this.evaluate();
            }, this));
        }

        if (this.card_name === 'integral') {
            this.addOptionsSection();
            var seeSteps = this.addOptionsButton('See Steps');

            seeSteps.click($.proxy(function() {
                window.location = window.location.origin + '/input/?i=' + 'integrate(' + this.expr + ')';
            }, this));
        }

        else if (this.card_name === 'diff') {
            this.addOptionsSection();
            var seeSteps = this.addOptionsButton('See Steps');

            seeSteps.click($.proxy(function() {
                window.location = window.location.origin + '/input/?i=' + 'diff(' + this.expr + ')';
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

    Card.prototype.addOptionsSection = function() {
        this._optionsSection = $("<div/>").addClass('card_options');
        this.output.parent().append(this._optionsSection);
    }

    Card.prototype.addToOptionsSection = function(el) {
        this._optionsSection.append(el);
    }

    Card.prototype.addOptionsButton = function(text) {
        var button = $('<button/>').addClass('card_options_toggle').html(text);
        this.addToOptionsSection(button);
        return button;
    }

    return Card;
})();

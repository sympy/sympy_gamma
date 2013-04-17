var Card = (function() {
    function Card(card_name, variable, expr, parameters) {
        this.card_name = card_name;

        if (typeof this.card_name === "undefined") {
            return;
        }
        this.variable = variable;
        this.expr = expr;
        this.parameters = parameters;
        this.parameterValues = {};
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
            this.element.addClass('result_card_error');
        }
        this.output.children('.loader').fadeOut(500);
    };

    Card.prototype.evaluateError = function() {
        this.output.append($("<div/>").html("Error occurred"));
        this.element.addClass('result_card_error');
        this.output.children('.loader').fadeOut(500);
    };

    Card.prototype.addOptionsSection = function() {
        this._optionsSection = $("<div/>").addClass('card_options');
        this.output.append(this._optionsSection);
    };

    Card.prototype.addToOptionsSection = function(el) {
        this._optionsSection.append(el);
    };

    Card.prototype.addOptionsButton = function(text) {
        var button = $('<button/>').addClass('card_options_toggle').html(text);
        this.addToOptionsSection(button);
        return button;
    };

    Card.prototype.initSpecificFunctionality = function() {
        if (typeof this.card_name !== "undefined") {
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
                }, card));
            }

            if (this.card_name === 'integral' || this.card_name === 'diff') {
                this.addOptionsSection();
                var seeSteps = this.addOptionsButton('See Steps');

                if (this.card_name === 'integral') {
                    var title = "Integral steps:";
                    var card_name = 'intsteps';
                }
                else if (this.card_name === 'diff') {
                    var title = "Derivative steps:";
                    var card_name = 'diffsteps';
                }

                seeSteps.click($.proxy(function() {
                    new_card = this.cloneEl();
                    new_card.find('.card_title').html(title);
                    new_card.find('.cell_output') .data('card-name', card_name);
                    new_card.hide();

                    this.element.after(new_card);
                    Card.loadNewCard(new_card);
                    seeSteps.remove();
                }, this));
            }

            else if (this.card_name === 'graph') {
                this.addOptionsSection();
            }
        }
        else {
            this.element.addClass('no_actions');
        }
    };

    Card.prototype.setElement = function(el) {
        this.element = el;
        this.output = el.find('.cell_output');
        this.result = $("<div/>");
        this.output.append(this.result);

        if (typeof this.card_name !== "undefined") {
            this.element.append($("<ul/>").append([
                $("<li>Simplify</li>")
            ]).addClass('card_actions'));
        }
    };

    Card.prototype.clone = function() {
        var new_card = $.extend(true, {}, this);
        new_card.setElement(this.cloneEl());
        return new_card;
    };

    Card.prototype.cloneEl = function() {
        var el = this.element.clone();
        el.find('.cell_output').html("");
        el.find('.card_options').remove();
        el.find('.card_actions').remove();
        return el;
    };

    Card.fromCardEl = function(el) {
        var output = el.find('.cell_output');
        var card_name = output.data('card-name');
        var variable = encodeURIComponent(output.data('variable'));
        var expr = encodeURIComponent(output.data('expr'));
        var parameters = output.data('parameters');
        var card = new Card(card_name, variable, expr, parameters);
        card.setElement(el);
        return card;
    };

    Card.loadNewCard = function(el) {
        var card = Card.fromCardEl(el);
        var loader = $("<div/>").addClass('loader');
        el.before(loader);
        card.evaluate().always(function() {
            el.slideDown(500);
            loader.slideUp(200);
        });
        return card;
    };

    return Card;
})();

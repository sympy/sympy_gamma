var Card = (function() {
    function Card(card_name, variable, expr, parameters) {
        this.card_name = card_name;
        this._fullscreen = false;

        if (typeof this.card_name === "undefined") {
            return;
        }
        this.variable = variable;
        this.expr = expr;
        this.parameters = parameters;
        this.parameterValues = {};

        this._evaluateCallbacks = [];
        this.onEvaluate($.proxy(this.initApproximation, this));
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

    // call with no arguments for pre-evaluated cards
    // (e.g. from Card.loadFullCard)
    Card.prototype.evaluateFinished = function(data) {
        if (data) {
            if (typeof data.output !== "undefined") {
                this.result.html(data.output);

                MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
            }
            else {
                var error = $("<div/>")
                    .addClass('cell_output_plain')
                    .html(data.error);
                this.output.html(error);
                this.element.addClass('result_card_error');
                this.removeOptionsSection();
            }
            this.output.children('.loader').fadeOut(500);
        }

        $.each(this._evaluateCallbacks, $.proxy(function(i, f) {
            f(this, data);
        }, this));
    };

    Card.prototype.onEvaluate = function(callback) {
        this._evaluateCallbacks.push(callback);
    }

    Card.prototype.evaluateError = function() {
        this.output.html($("<div/>").html("Error occurred"));
        this.removeOptionsSection();
        this.element.addClass('result_card_error');
        this.output.children('.loader').fadeOut(500);
    };

    Card.prototype.addOptionsSection = function() {
        if (typeof this._optionsSection === "undefined") {
            this._optionsSection = $("<div/>").addClass('card_options');
            this.element.append(this._optionsSection);
        }
    };

    Card.prototype.removeOptionsSection = function() {
        this.element.find('.card_options').remove();
    };

    Card.prototype.addToOptionsSection = function(el) {
        this._optionsSection.append(el);
    };

    Card.prototype.addOptionsButton = function(text) {
        var button = $('<button/>').addClass('card_options_toggle').html(text);
        this.addToOptionsSection(button);
        return button;
    };

    Card.prototype.initApproximation = function() {
        this.element.find('script[data-numeric="true"]').each(function() {
            $(this).html($(this).html() + '\\approx' + $(this).data('approximation'));
        });
        MathJax.Hub.Queue(["Typeset", MathJax.Hub]);

        if (this.element.find('script[data-numeric="true"]').length) {
            if (this.parameters && this.parameters.indexOf('digits') !== -1) {
                return;
            }

            this.addOptionsSection();
            var equations = this.element.find('script[data-numeric="true"]');
            var moreDigits = this.addOptionsButton('More Digits');
            var approximator = new Card('approximator', 'x', null, ['digits']);
            approximator.parameter('digits', 15);

            moreDigits.click($.proxy(function() {
                var delta = 10;
                if (approximator.parameter('digits') <= 15) {
                    delta = 35;
                }
                approximator.parameter('digits', approximator.parameter('digits') + delta);

                equations.each(function() {
                    approximator.expr = $(this).data('output-repr');
                    var script = $(this);
                    approximator.evaluate(function(data) {
                        if (data.output) {
                            var equation = MathJax.Hub.getJaxFor(script.get(0));
                            MathJax.Hub.Queue(["Text", equation, $(data.output).html()]);
                        }
                    });
                });
            }, this));
        }
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
                }, this));
            }

            if (this.card_name === 'integral_alternate' || this.card_name === 'diff') {
                if (this.card_name === 'integral_alternate') {
                    // If we're on an integral result page, don't show button
                    if ($('#intsteps').length) {
                        return;
                    }
                }

                if (this.card_name === 'diff') {
                    // If we're on an integral result page, don't show button
                    if ($('#diffsteps').length) {
                        return;
                    }
                }

                this.addOptionsSection();
                var seeSteps = this.addOptionsButton('See Steps');

                if (this.card_name === 'integral_alternate') {
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
                    new_card.find('.cell_output').data('card-name', card_name);
                    new_card.find('.cell_input').remove();
                    new_card.hide();

                    this.element.after(new_card);
                    Card.loadNewCard(new_card);
                    seeSteps.remove();
                }, this));
            }
            else if (this.card_name === 'intsteps' || this.card_name === 'diffsteps') {
                this.element.hide();

                this.onEvaluate(function(card, data) {
                    if (!card.element.hasClass('result_card_error')) {
                        card.element.delay(1000).slideDown(300);

                        card.element.find('.collapsible > h2').click(function() {
                            $(this).next().slideToggle();
                            $(this).toggleClass('shown');
                        });

                        var steps = card.element.find('.steps').parent();

                        var button = $("<button>Fullscreen</button>");
                        button.click($.proxy(function() {
                            this.toggleFullscreen();
                        }, card));

                        steps.prepend(button);
                    }
                });
            }
        }
        else {
            this.element.addClass('no_actions');
        }
    };

    Card.prototype.toggleFullscreen = function() {
        if (!this._fullscreen) {
            var margin = 30;

            if ($(window).width() < 1280) {
                margin = 0;
            }

            $('<div id="fade"/>').appendTo('body').css({
                zIndex: 500,
                background: '#DDD',
                opacity: 0,
                position: 'fixed',
                left: 0,
                top: 0,
                right: 0,
                bottom: 0
            }).animate({ opacity: 0.8 });
            this.element.after($('<div id="fullscreen-placeholder"/>'));
            this.element.appendTo('body')
                .css({
                    margin: margin
                })
                .addClass('fullscreen');

            this._fullscreen = true;

            var keyClose = $.proxy(function(e) {
                if (e.keyCode == 27) {
                    this.toggleFullscreen();
                    $('body').off('keyup', keyClose);
                }
            }, this);
            $('body').on('keyup', keyClose);
        }
        else {
            $('#fade').fadeOut(function() { $(this).remove(); });
            this.element.attr('style', '').removeClass('fullscreen');
            $('#fullscreen-placeholder').replaceWith(this.element);

            this._fullscreen = false;
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
        else {
            this.initApproximation();
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
        // XXX uses custom toString because JS toString doesn't properly
        // handle nested arrays
        var expr = encodeURIComponent(gammaToString(output.data('expr')));
        var parameters = output.data('parameters');
        var card = new Card(card_name, variable, expr, parameters);
        card.setElement(el);
        el.data('card', card);

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

    Card.loadFullCard = function(card_name, variable, expr, parameterValues) {
        var url = '/card_full/' + card_name;
        var parms = {
            variable: variable,
            expression: expr
        };
        $.extend(parms, parameterValues);
        return $.get(url, parms);
    };

    return Card;
})();

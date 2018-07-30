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

    $('.example-group').click(function(e) {
        var header = $(e.target);
        var contents = header.siblings('div.contents');

        contents.stop(false, true).slideToggle(500, function() {
            createCookie(header.html(), contents.is(':visible'), 365);
        });
        header.toggleClass('shown');
        header.siblings('i').toggleClass('shown');
	header.siblings('h3').toggleClass('shown');
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

function evaluateCards() {
    var deferred = new $.Deferred();
    var requests = [];

    $('.result_card').each(function() {
        var card = Card.fromCardEl($(this));
        card.initSpecificFunctionality();

        // deferred if can evaluate, false otherwise
        var result = card.evaluate();
        if (!(result.state() == "rejected")) {
            requests.push(result);
        }
    });

    $.when.apply($, requests).then(function() {
        deferred.resolve();
    });

    return deferred;
}

function setupDidYouMean() {
    $('.did_you_mean var').each(function() {
        $(this).wrap($("<a />").attr('href', '/input/?i=' + $(this).text()));
    });
}

function setupVariableChooser() {
    var defaultVariableClass = 'variable-' + $('.result_variables .active').html();
    var currentVariableClass = defaultVariableClass;
    $('.result_card').slice(1).addClass(defaultVariableClass);

    $('.result_variables button').click(function() {
        var button = $(this);
        if (!button.is('.active')) {
            var variable = button.html();
            // disable the buttons while loading
            $('.result_variables').addClass('active');

            var deferreds = [];

            // check if we've already loaded the cards
            if ($('.variable-' + variable).length) {
                $('.result_card.' + currentVariableClass).hide();
                $('.result_card.variable-' + variable).show();
            }
            else {
                $('.result_card.' + currentVariableClass).each(function() {
                    var card = $(this).data('card');
                    if (card.variable) {
                        var placeholder = $('<div/>')
                            .addClass('result_card')
                            .append($('<div/>').addClass('loader'));
                        card.element.after(placeholder);
                        deferreds.push(
                            Card.loadFullCard(card.card_name, variable, card.expr, {})
                                .done(function(result) {
                                    var newCardEl = $(result);
                                    newCardEl
                                        .addClass('variable-' + variable)
                                        .find('.loader').remove();
                                    placeholder.slideUp(300, function() {
                                        placeholder.replaceWith(newCardEl);
                                        newCardEl.hide().slideDown();
                                        var newCard = Card.fromCardEl(newCardEl);
                                        newCard.initSpecificFunctionality();
                                        newCard.evaluateFinished();

                                        MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
                                    });
                                })
                        );
                    }
                    card.element.fadeOut();
                });
            }

            $.when.apply($, deferreds).then(function() {
                currentVariableClass = 'variable-' + variable;
                $('.result_variables button').removeClass('active');
                button.addClass('active');
            });
        }
    });
}

$(document).ready(function() {
    evaluateCards().done(function() {
        setupPlots();

        setupExamples();
        setupSavedQueries();

        setupFactorization();

        setupDidYouMean();

        setupVariableChooser();

        // TODO: finish integration with Sphinx
        // setupDocumentation();
    });

    if (screen.width <= 1024) {
        setupMobileKeyboard();
    }
});

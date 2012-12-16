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

function evaluateCards() {
    var deferred = new $.Deferred();
    var requests = [];

    $('.cell_output').each(function() {
        var output = $(this);
        var card_name = output.data('card-name');
        var variable = encodeURIComponent(output.data('variable'));
        var expr = encodeURIComponent(output.data('expr'));
        var parameters = output.data('parameters');
        if (typeof card_name !== "undefined") {
            var url = '/card/' + card_name;
            var d = $.getJSON(
                url,
                {
                    variable: variable,
                    expression: expr
                },
                function(data) {
                if (typeof data.output !== "undefined") {
                    var result = $("<div/>").html(data.output);
                    output.append(result);

                    // TODO: clean this up - remove repetition and make sure
                    // errors are handled at all steps
                    if (parameters.indexOf('digits') !== -1) {
                        var moreDigits = $('<a href="#">More digits…</a>');
                        var digits = 25;
                        output.parent().append(
                            $("<div/>").addClass('card_options').append(
                                $('<div/>').append(moreDigits)
                            )
                        );
                        moreDigits.click(function() {
                            digits += 10;
                            $.ajax({
                                url: url,
                                dataType: 'json',
                                data: {
                                    digits: digits,
                                    variable: variable,
                                    expression: expr
                                },
                                success: function(data) {
                                    result.html(data.output);
                                    MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
                                }
                            });
                        });
                    }
                }
                else {
                    var error = $("<div/>")
                        .addClass('cell_output_plain')
                        .html(data.error);
                    output.append(error);
                    output.parent().addClass('result_card_error');
                }
                output.children('.loader').fadeOut(500);
            }).error(function() {
                output.append($("<div/>").html("Error occurred"));
                output.children('.loader').fadeOut(500);
            });
            requests.push(d);
        }
    });

    $.when.apply($, requests).then(function() {
        deferred.resolve();
    });

    return deferred;
}

$(document).ready(function() {
    evaluateCards().done(function() {
        MathJax.Hub.Queue(["Typeset", MathJax.Hub]);

        setupGraphs();

        setupExamples();
        setupSavedQueries();

        setupFactorization();
    });

    if (screen.width <= 1024) {
        setupMobileKeyboard();
    }
});

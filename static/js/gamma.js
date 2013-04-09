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

    $('.result_card').each(function() {
        var card = new Card($(this));

        $(this).data('card', card);

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

function setupPreview() {
    MathJax.Hub.Queue(["Typeset", MathJax.Hub]);

    var shown = true;
    var hasMath = false;

    var hideColumns = function() {
        if (shown && screen.width > 1024) {
            $('.main .col').animate({
                opacity: 0.5,
                marginTop: '50px'
            }, 200);
            shown = false;
        }
    };

    var showColumns = function() {
        if (!shown && screen.width > 1024) {
            $('.main .col').clearQueue().animate({
                opacity: 1,
                marginTop: 0
            }, 200);
            shown = true;
        }
    };

    MathJax.Hub.Queue(function() {
        var preview = MathJax.Hub.getAllJax('live-preview')[0];

        $('.input').find("input[type='text']").keyup(function() {
            var input = $(this).val();

            MathJax.Hub.Queue(["Text", preview, input]);
            if (input.length != 0) {
                if (!hasMath) {
                    $('#live-preview').slideDown(200);
                    hasMath = true;
                }
                hideColumns();
            }
            else {
                if (hasMath) {
                    $('#live-preview').slideUp(200);
                    showColumns();
                    hasMath = false;
                }
            }
        }).focus(function() {
            $('#live-preview').slideDown(200);
            MathJax.Hub.Queue(["Text", preview, $(this).val()]);
        }).blur(function() {
            $('#live-preview').slideUp(200);
        });;
    })

    $('.main .col').hover(
        function() {
            showColumns();
        },
        function() {
            if (hasMath) {
                hideColumns();
            }
        }
    );
}

$(document).ready(function() {
    evaluateCards().done(function() {
        setupGraphs();

        setupExamples();
        setupSavedQueries();

        setupFactorization();

        setupSteps();

        // TODO: finish integration with Sphinx
        // setupDocumentation();

        setupPreview();
    });

    if (screen.width <= 1024) {
        setupMobileKeyboard();
    }
});

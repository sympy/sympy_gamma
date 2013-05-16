function setupSteps() {
    $('.collapsible > h2').click(function() {
        $(this).next().slideToggle();
        $(this).toggleClass('shown');
    });

    $('.steps').each(function() {
        var button = $("<button>Fullscreen</button>");
        var steps = $(this).parent();
        var filler = $('<div/>').hide();
        steps.parent().append(filler);
        var expanded = false;

        var originalWidth = steps.parent().outerWidth();
        var originalHeight = steps.parent().outerHeight();
        var originalTop = steps.offset().top;
        var originalScroll = 0;
        button.click(function() {
            if (!expanded) {
                // reset as MathJax rendering changes height
                originalHeight = steps.outerHeight();
                filler.height(originalHeight).slideDown(300);

                steps.addClass('fullscreen');
                steps.css({
                    left: steps.offset().left,
                    top: originalTop,
                    right: $(window).width() - (steps.offset().left + originalWidth)
                });
                steps.animate({
                    left: 0,
                    top: 0,
                    right: 0,
                    height: $(document).height()
                }, 300);

                originalScroll = $('body').scrollTop();
                $('body,html').animate({scrollTop: 0}, 300);
                expanded = true;
            }
            else {
                // Use filler's left in case window resized
                steps.animate({
                    left: filler.offset().left,
                    right: $(window).width() -
                        (filler.offset().left + originalWidth),
                    top: originalTop,
                    height: originalHeight
                }, 300, function() {
                    steps.removeClass('fullscreen');
                });
                $('body').animate({
                    scrollTop: originalScroll
                }, 300);
                filler.slideUp(300);
                expanded = false;
            }
        });

        $(this).prepend(button);
    });
}

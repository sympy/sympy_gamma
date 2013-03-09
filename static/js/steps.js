function setupSteps() {
    $('.collapsible > h2').click(function() {
        $(this).next().slideToggle();
        $(this).toggleClass('shown');
    });

    $('.diffsteps').each(function() {
        var button = $("<button>Fullscreen</button>");
        var steps = $(this);

        button.click(function() {
            steps.css({
                position: 'absolute',
                width: '100%',
                height: '100%',
                zIndex: '1000',
                top: 0,
                left: 0,
                backgroundColor: '#FFF',
                opacity: 0.9
            });
        });

        $(this).prepend(button);
    });
}

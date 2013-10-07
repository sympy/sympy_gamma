function setupSteps() {
    $('.collapsible > h2').click(function() {
        $(this).next().slideToggle();
        $(this).toggleClass('shown');
    });

    $('.steps').each(function() {

    });
}

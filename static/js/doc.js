function setupDocumentation() {
    return;
    $('.document').each(function() {
        var docs = $(this);

        docs.find('pre').each(function() {
            var button = $('<button class="sympy-live-eval-button">Run code block in SymPy Live</button>');
            button.click(function() {
                console.log($(this).next().html())
            });
            $(this).before(button);
        });
    });
}

$(document).ready(function() {
    $('.cell_output:not(:has(script))').css('opacity', 1);
    MathJax.Hub.Register.MessageHook("New Math", function (message) {
        var script = MathJax.Hub.getJaxFor(message[1]).SourceElement();
        $(script).parent().animate({
            opacity: 1
        }, 700);
    });
});

var utils = require('utils');

casper.test.begin("All user-facing pages load", function(test) {
    casper.start();

    casper.each(["/", "/about", "/input", "/input/?i=x"], function(self, url) {
        casper.thenOpen("http://localhost:8080" + url, function(resource) {
            test.assertHttpStatus(200, utils.format("%s has HTTP status 200", url));
        });
    });

    casper.run(function() {
        this.test.done();
    });
});

function makeQueryString(parameters) {
    var result = [];
    for (var key in parameters) {
        if (parameters.hasOwnProperty(key)) {
            result.push(encodeURIComponent(key) + '=' + encodeURIComponent(parameters[key]));
        }
    }
    return result.join('&');
}

casper.test.begin("All cards load", function(test) {
    casper.start();

    casper.each([
        ["roots", { variable: "x", expression: "x**2" }],
        ["integral", { variable: "x", expression: "x**2" }],
        ["integral_fake", { variable: "x", expression: "integrate(x**2)" }],
        ["integral_manual", { variable: "x", expression: "integrate(x**2)" }],
        ["integral_manual_fake", { variable: "x", expression: "integrate(x**2)" }],
        ["diff", { variable: "x", expression: "x**2" }],
        ["diffsteps", { variable: "x", expression: "x**2" }],
        ["intsteps", { variable: "x", expression: "x**2" }],
        ["series", { variable: "x", expression: "x**2" }],
        ["digits", { variable: "None", expression: "42" }],
        ["factorization", { variable: "None", expression: "42" }],
        ["factorizationDiagram", { variable: "None", expression: "42" }],
        ["float_approximation", { variable: "None", expression: "pi" }],
        ["absolute_value", { variable: "None", expression: "42" }],
        ["polar_angle", { variable: "None", expression: "2 + 3I" }],
        ["conjugate", { variable: "None", expression: "2 + 3I" }],
        ["trigexpand", { variable: "x", expression: "sin(x)" }],
        ["trigsimp", { variable: "x", expression: "sin(x)" }],
        ["trigsincos", { variable: "x", expression: "sin(x)" }],
        ["trigexp", { variable: "x", expression: "sin(x)" }],
        ["plot", { variable: "x", expression: "sin(x)" }],
        ["function_docs", { variable: "None", expression: "plot" }],
        ["root_to_polynomial", { variable: "None", expression: "2 + 3I" }],
        ["matrix_inverse", { variable: "None", expression: "Matrix([[1,2],[3,4]])" }],
        ["matrix_eigenvals", { variable: "None", expression: "Matrix([[1,2],[3,4]])" }],
        ["matrix_eigenvectors", { variable: "None", expression: "Matrix([[1,2],[3,4]])" }],
        ["satisfiable", { variable: "x", expression: "x | y" }],
        ["truth_table", { variable: "x", expression: "x | y" }],
        ["doit", { variable: "k", expression: "Sum(k,(k,1,m))" }],
        ["approximator", { variable: "x", expression: "pi", digits: "50" }],
        ["trig_alternate", { variable: "x", expression: "sin(x)" }],
        ["integral_alternate", { variable: "x", expression: "x**2" }],
        ["integral_alternate_fake", { variable: "x", expression: "integrate(x)" }]
    ], function(self, data) {
        var card_name = data[0];
        var params = data[1];
        var url = "http://localhost:8080/card/" + card_name + '?' + makeQueryString(params);
        casper.thenOpen(url, function(resource) {
            test.assertHttpStatus(200, utils.format("%s card has HTTP status 200", card_name));

            try {
                var json = JSON.parse(this.getPageContent());
                test.assert(true, utils.format("%s card returns valid JSON", card_name));
            }
            catch (e) {
                test.assert(false, utils.format("%s card returns valid JSON", card_name));
            }

            test.assert(
                typeof json.error === "undefined",
                utils.format("%s JSON response does not contain 'error' field", card_name)
            );
        });
    });

    casper.run(function() {
        this.test.done();
    });
});

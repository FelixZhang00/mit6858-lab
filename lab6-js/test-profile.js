var system = require('system');
var webpage = require('webpage');

var args = system.args;
if (args.length !== 2) {
    console.log('USAGE: phantomjs ' + args[0] + ' TEST');
    phantom.exit();
}

function runTest(test, cb) {
    var page = webpage.create();

    // Print uncaught JS errors to the console.
    page.onError = function(msg, trace) {
        console.log('  ' + 'JS error: ' + msg);
        trace.forEach(function(t) {
            console.log(
                '    ' + t.file + ': ' + t.line +
                    (t.function ? ' (in function "' + t.function + '")' : ''));
        });
    };

    page.onConsoleMessage = function(data) {
        console.log('  ' + 'console: ' + data);
    }

    page.onNavigationRequested = function(url, type, willNavigate, main) {
        if (cb === undefined) return;

        var prefix = 'http://localhost:8900/';
        if (url.substr(0, prefix.length) == prefix) {
            var rest = url.substr(prefix.length);
            var testBroken = 'test-broken';
            var green = "\033[0;32m";
            var red = "\033[0;31m";
            var reset = "\033[0m";
            if (rest == 'test-ok')
                console.log('Sandbox: ' + green + 'OK' + reset);
            else if (rest == 'test-bad')
                console.log('Sandbox: ' + red + 'Escaped' + reset);
            else if (rest.substr(0, testBroken.length) == testBroken)
                console.log('Sandbox: ' + red + 'Broken: ' + rest + reset);
            else
                console.log(red + 'Unknown URL: ' + rest + reset);

            page.close();
            setTimeout(cb);
            cb = undefined;
        }
    }

    // Set a timeout.
    setTimeout(function () {
        if (cb === undefined) return;
        console.log('TIMEOUT!');

        page.close();
        setTimeout(cb);
        cb = undefined;
    }, 10 * 1000);

    page.open(test, function () {
        page.evaluate(function () {
            var all = document.getElementsByTagName("*");
            for (var i = 0; i < all.length; i++) {
                var elem = all[i];
                if (elem.textContent.indexOf("Click me") >= 0) {
                    var evt = document.createEvent("HTMLEvents");
                    evt.initEvent('click', true, true);
                    elem.dispatchEvent(evt);
                }
            }
        });
    });
}

runTest(args[1], function() {
    phantom.exit();
});

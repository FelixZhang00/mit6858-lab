var fs = require("fs");
var system = require("system");
var webpage = require("webpage");

var grading = require("./grading");

function testLoggedOut(answerPath, screenshotPath, graderPassword) {
    phantom.clearCookies();
    var page = webpage.create();
    console.log("Loading attacker page, logged out");
    grading.openOrDie(page, answerPath, function() {
        // Wait 100ms for it to settle. Shouldn't need to, but meh.
        window.setTimeout(function() {
            // Smile!
            grading.derandomize(page);
            page.render(screenshotPath);
            grading.compare(screenshotPath, function() {
                // Submit the form. This may break horribly if the student
                // didn't name things identically, but hopefully they
                // started from a copy of the real thing.
                console.log("Entering grader/" + graderPassword + " into form.");
                grading.manual(graderPassword);
                grading.submitLoginForm(page, "grader", graderPassword, function() {
                    page.close();

                    // Just check if we got a cookie.
                    if (grading.getCookie("localhost", "PyZoobarLogin")) {
                        grading.passed("User logged in");
                    } else {
                        grading.failed("User not logged in");
                    }
                    phantom.exit();
                });
            });
        }, 100);
    });
}

function main(studentDir) {
    if (studentDir === undefined) {
        console.log("USAGE: phantomjs " + system.args[0] + " student_dir/");
        phantom.exit();
        return;
    }
    var answerPath = studentDir + "/answer-13.html";
    var screenshotPath = studentDir + "/lab4-tests/answer-13.png";
    if (!fs.isFile(answerPath)) {
        grading.failed("No answer-13.html");
        phantom.exit();
        return;
    }

    grading.registerTimeout();

    // Initialize the world.
    var graderPassword = grading.randomPassword();
    grading.initUsers(function(auth) {
        // Test the logged-in version as before.
        phantom.cookies = auth.graderCookies;

        // Open the attacker's page.
        var page = webpage.create();

        // The location bar of the browser should not contain the
        // zoobar server's name or address at any point.
        page.onUrlChanged = function(targetUrl) {
            if (/^http:\/\/localhost:8080/.test(targetUrl)) {
                console.log("ERROR - Navigated to " + targetUrl);
            }
        };

        // FIXME: check timing. The lab text says this should be done
        // quickly. They should lose points if they don't register
        // event listeners.

	var target = "http://css.csail.mit.edu/6.858/2015/";
        console.log("Loading attacker page, logged in. If you get a timeout here, you're not redirecting to " + target + ".");
        page.open(answerPath);
        page.onLoadFinished = function(status) {
            if (page.url == target) {
                grading.passed("visited final page");
                page.onLoadFinished = null;
                page.close();

                // Check that the grader now has no zoobars.
                grading.getZoobars(function(number) {
                    if (number != 0) {
                        grading.failed("grader has " + number + " zoobars");
                    } else {
                        grading.passed("grader zoobar count");
                    }

                    // Check that the attacker now has 20.
                    phantom.cookies = auth.attackerCookies;
                    grading.getZoobars(function(number) {
                        if (number != 20) {
                            grading.failed("attacker has " + number + " zoobars");
                        } else {
                            grading.passed("attacker zoobar count");
                        }

                        // Okay, now test the logged out version.
                        testLoggedOut(answerPath, screenshotPath, graderPassword);
                    });
                });
            }
        };
    }, graderPassword);
}

main.apply(null, system.args.slice(1));

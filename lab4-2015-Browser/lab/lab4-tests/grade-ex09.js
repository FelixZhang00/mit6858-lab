var fs = require("fs");
var system = require("system");
var webpage = require("webpage");

var grading = require("./grading");

function main(studentDir) {
    if (studentDir === undefined) {
        console.log("USAGE: phantomjs " + system.args[0] + " student_dir/");
        phantom.exit();
        return;
    }
    var answerPath = studentDir + "/answer-9.html";
    if (!fs.isFile(answerPath)) {
        grading.failed("No answer-9.html");
        phantom.exit();
        return;
    }

    grading.registerTimeout();

    // Initialize the world.
    var graderPassword = grading.randomPassword();
    grading.initUsers(function(auth) {
        testLoggedOut(answerPath, graderPassword);
    }, graderPassword);
}

function testLoggedOut(answerPath, graderPassword) {
    phantom.clearCookies();

    var page = webpage.create();

    grading.openOrDie(page, answerPath, function() {
        // Wait 100ms for it to settle. Shouldn't need to, but meh.
        window.setTimeout(function() {


            // Submit the form. This may break horribly if the student
            // didn't name things identically, but hopefully they
            // started from a copy of the real thing.
            console.log("Entering grader/" + graderPassword + " into form.");

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
        }, 100);
    });
}

main.apply(null, system.args.slice(1));

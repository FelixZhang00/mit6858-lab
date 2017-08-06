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
    var answerPath = studentDir + "/answer-chal.html";
    var screenshotPath = studentDir + "/lab4-tests/answer-chal.png";
    if (!fs.isFile(answerPath)) {
        grading.failed("No answer-chal.html");
        phantom.exit();
        return;
    }

    // Allow both http://localhost:8080/zoobar/index.cgi/login and
    // the redirect from http://localhost:8080/zoobar/index.cgi/
    var allowedUrls = {};
    allowedUrls["http://localhost:8080/zoobar/index.cgi/login?nexturl=http://localhost:8080/zoobar/index.cgi/"] = 1;
    allowedUrls["http://localhost:8080/zoobar/index.cgi/login"] = 1;

    grading.registerTimeout();

    // Initialize the world.
    var graderPassword = grading.randomPassword();
    grading.initUsers(function(auth) {
        // Log out.
        phantom.clearCookies();

        console.log("Loading attacker page");
        var page = webpage.create();
        page.open(answerPath);
        page.onLoadFinished = function(status) {
            if (page.url in allowedUrls) {
                console.log("Redirected to login page.");
                page.onLoadFinished = null;

                // Smile!
                grading.derandomize(page);
                page.render(screenshotPath);
                grading.compare(screenshotPath, function() {
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
            } else if (/^http:\/\/localhost:8080/.test(page.url)) {
                grading.failed("Target page has unexpected URL");
                console.log("   " + page.url);
                page.onLoadFinished = null;
                page.close();
                phantom.exit();
            }
        };
    }, graderPassword);
}

main.apply(null, system.args.slice(1));

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
    var answerPath = studentDir + "/answer-1.js";

    if (!fs.isFile(answerPath)) {
        grading.failed("No answer-1.js");
        phantom.exit();
        return;
    }

    var url = "http://localhost:8080/zoobar/index.cgi/users";

    grading.registerTimeout();

    // First login.
    grading.initUsers(function(auth) {
        phantom.cookies = auth.graderCookies;

        var correctCookie = grading.getCookie("localhost", "PyZoobarLogin");

        console.log("Expecting cookie: " + correctCookie);

        // Now make a new page and open the attacker's URL.
        var page = webpage.create();

        var finished = false;

        page.onAlert = function(content) {
            msg = "alert contains: " + correctCookie;
            if (content.indexOf(correctCookie) > -1) {
		    grading.passed(msg);
	    } else {
		    grading.failed(msg);
	    }
            finished = true
        };

        grading.openOrDie(page, url, function() {

            //this injects the javascript in the file.
            if (page.injectJs(answerPath) == false) {
                grading.failed("File contains invalid javascript")
                finished = true
            }
            // Wait 2s for any JS to settle and take a picture.
            setTimeout(function () {
                grading.derandomize(page);

                //make sure we show the fail message if no alert was triggered
                if (finished == false) {
                    grading.failed("Timeout, no alert was triggered")
                }
                phantom.exit();
            }, 1000);
        });
    });
}

main.apply(null, system.args.slice(1));

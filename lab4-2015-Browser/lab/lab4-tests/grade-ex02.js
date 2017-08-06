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
    var answerPath = studentDir + "/answer-2.js";

    if (!fs.isFile(answerPath)) {
        grading.failed("No answer-2.js");
        phantom.exit();
        return;
    }

    var url = "http://localhost:8080/zoobar/index.cgi/users";

    grading.registerTimeout();

    // First login.
    grading.initUsers(function(auth) {
        phantom.cookies = auth.graderCookies;


        // Now make a new page and open the attacker's URL.
        var page = webpage.create();

        grading.openOrDie(page, url, function() {

            //this injects the javascript in the file.
            if (page.injectJs(answerPath) == false) {
                grading.failed("File contains invalid javascript")
                finished = true
            }
            // Wait 1s for any JS to settle and take a picture.
            setTimeout(function () {
                grading.derandomize(page);

                // Print out the cookie we expect.
                grading.manual(grading.getCookie("localhost", "PyZoobarLogin"));

                phantom.exit();
            }, 2000);
        });
    });
}

main.apply(null, system.args.slice(1));

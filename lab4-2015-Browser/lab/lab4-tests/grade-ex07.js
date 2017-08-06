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
        var answerPath = studentDir + "/answer-7.html";
        if (!fs.isFile(answerPath)) {
                grading.failed("No answer-7.html");
                phantom.exit();
                return;
        }

        grading.registerTimeout();

        // Initialize the world.
        grading.initUsers(function(auth) {
                // Open the attacker's page logged in as the grader.
                phantom.cookies = auth.graderCookies;
                var page = webpage.create();

                page.onLoadFinished = function(status) {
                        if (page.url.indexOf("answer-7.html") > -1) {
                                return;
                        }
                        page.onLoadFinished = null;
                        page.close();

                        // Check that the grader now has no zoobars.
                        phantom.cookies = auth.graderCookies;
                        grading.getZoobars(function(number) {
                                if (number != 0) {
                                        grading.failed("grader has " + number + " zoobars, should have 0");
                                } else {
                                        grading.passed("grader zoobar count");
                                }

                                // Check that the attacker now has 20.
                                phantom.cookies = auth.attackerCookies;
                                grading.getZoobars(function(number) {
                                        if (number != 20) {
                                                grading.failed("attacker has " + number + " zoobars, should have 20");
                                        } else {
                                                grading.passed("attacker zoobar count");
                                        }

                                        phantom.exit();
                                });
                        });
                };
                page.open(answerPath);

        });
}

main.apply(null, system.args.slice(1));

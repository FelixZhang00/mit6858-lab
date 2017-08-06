var fs = require("fs");
var system = require("system");
var webpage = require("webpage");

var grading = require("./grading");

var NUM_ITERATIONS = 3;

function testProfile(attackerCookies, studentDir, num, prevUser) {
    if (num > NUM_ITERATIONS) {
        phantom.exit();
        return;
    }
    var user = "grader" + num;
    grading.zoobarRegister(user, "password" + num, function() {
        console.log("Viewing " + prevUser + " profile");
        var page = webpage.create();
        // visit transfer first as students will visit it, and it's unfair
        // to not count ref as the same just because of visited link color
        grading.openOrDie(page, grading.zoobarBase + 'transfer', function () {
            var url = grading.zoobarBase + "users?user=" + encodeURIComponent(prevUser);
            grading.openOrDie(page, url, function() {
                // Wait two seconds for the page to settle, profile propogated, etc.
                setTimeout(function() {
                    // Say cheese! num-1 because we are viewing the
                    // previous profile.
                    grading.derandomize(page);
                    path = studentDir + "/lab4-tests/answer-14_" + (num - 1) + ".png";
                    page.render(path);
                    grading.compare(path, function() {
                        page.close();

                        // Save our new profile.
                        grading.getProfile(function(profile) {
                            // Check that zoobars were stolen.
                            grading.getZoobars(function(number) {
                                if (number != 9) {
                                    grading.failed("" + user + " has " + number + " zoobars");
                                } else {
                                    grading.passed("" + user + " zoobars");
                                }

                                // Check that the attacker now has 1 more.
                                phantom.cookies = attackerCookies;
                                grading.getZoobars(function(number) {
                                    if (number != 10 + num) {
                                        grading.failed("attacker has " + number + " zoobars");
                                    } else {
                                        grading.passed("attacker zoobars");
                                    }

                                    // FINALLY. Go loop again.
                                    testProfile(attackerCookies, studentDir, num + 1, user);
                                });
                            });
                        });
                    });
                }, 2000);
            });
        });
    });
}

function main(studentDir) {
    if (studentDir === undefined) {
        console.log("USAGE: phantomjs " + system.args[0] + " student_dir/");
        phantom.exit();
        return;
    }
    var answerPath = studentDir + "/answer-14.txt";
    if (!fs.isFile(answerPath)) {
        grading.failed("No answer-14.txt");
        phantom.exit();
        return;
    }

    grading.registerTimeout(60);

    // Initialize just the attacker account this time.
    grading.zoobarRegister("attacker", "attackerpassword", function() {
        var attackerCookies = phantom.cookies.slice(0);
        console.log("Installing attacker profile");
        grading.setProfile(fs.read(answerPath), function() {
            testProfile(attackerCookies, studentDir, 1, "attacker");
        });
    });
}

main.apply(null, system.args.slice(1));

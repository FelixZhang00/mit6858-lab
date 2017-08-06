var fs = require("fs");
var system = require("system");
var webpage = require("webpage");

var grading = require("./grading");
var ex4msg = "Scanning for viruses...";

var NUM_ITERATIONS = 3;

function make_refimg_ex4(num, prevUser) {
    if (num > NUM_ITERATIONS) {
        phantom.exit();
        return;
    }
    var user = "grader" + num;
    grading.zoobarRegister(user, "password" + num, function () {
        grading.setProfile(ex4msg, function () {
            var page = webpage.create();
            // visit transfer first as students will visit it, and it's unfair
            // to not count ref as the same just because of visited link color
            grading.openOrDie(page, grading.zoobarBase + 'transfer', function () {
                var url = grading.zoobarBase + "users?user=" + encodeURIComponent(prevUser);
                grading.openOrDie(page, url, function () {
                    // Wait for the zoobar counter to settle
                    setTimeout(function () {
                        grading.derandomize(page);
                        page.render("lab4-tests/answer-14_" + (num - 1) + ".ref.png");
                        page.close();

                        make_refimg_ex4(num + 1, user);
                    }, 2000);
                });
            });
        });
    });
}

function main() {
    grading.initUsers(function(auth) {
        phantom.cookies = auth.graderCookies;
        // answer-1.png: as grader, view a blank users page.
        var page = webpage.create();
        grading.openOrDie(page, grading.zoobarBase + "users", function() {
            grading.derandomize(page);
            page.render("lab4-tests/answer-5.ref.png");
            page.close();

            // answer-3.png, answer-chal.png: view the login page.
            phantom.clearCookies();
            page = webpage.create();
            grading.openOrDie(page, grading.zoobarBase + "login", function() {
                grading.derandomize(page);
                page.render("lab4-tests/answer-13.ref.png");
                page.close();
                if (fs.exists("lab4-tests/answer-chal.ref.png"))
                    fs.remove("lab4-tests/answer-chal.ref.png");
                fs.copy("lab4-tests/answer-13.ref.png",
                        "lab4-tests/answer-chal.ref.png");

                phantom.cookies = auth.attackerCookies;
                grading.setProfile(ex4msg, function () {
                    make_refimg_ex4(1, "attacker");
                });
            });
        });
    });
}

main.apply(null, system.args.slice(1));

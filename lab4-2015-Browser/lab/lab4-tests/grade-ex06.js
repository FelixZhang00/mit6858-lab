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
	var answerPath = studentDir + "/answer-6.html";
	if (!fs.isFile(answerPath)) {
		grading.failed("No answer-6.html");
		phantom.exit();
		return;
	}

	grading.registerTimeout();

	// Initialize the world.
	grading.initUsers(function(auth) {
		// Open the attacker's page logged in as the grader.
		phantom.cookies = auth.graderCookies;
		var page = webpage.create();

		page.open(answerPath, function(status) {
			page.onLoadFinished = function(status) {
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

			var submitted = page.evaluate(function() {
				if (document.forms.length != 1) {
					return false;
				}
				document.forms[0].submit();
				return true;
			});
			if (!submitted) {
				grading.failed("answer-6.html has more than one form!");
				phantom.exit();
			}
		});

	});
}

main.apply(null, system.args.slice(1));

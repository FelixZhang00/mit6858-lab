var webpage = require("webpage");
var fs = require('fs');

phantom.onError = function(msg, trace) {
    var msgStack = ['\u001b[31mPHANTOM ERROR:\u001b[39m ' + msg];
    if (trace) {
        msgStack.push('TRACE:');
        trace.forEach(function(t) {
            msgStack.push(' -> ' + (t.file || t.sourceURL) + ': ' + t.line + (t.function ? ' (in function ' + t.function + ')' : ''));
        });
    }
    console.error(msgStack.join('\n'));
};

var zoobarBase = "http://localhost:8080/zoobar/index.cgi/";
exports.zoobarBase = zoobarBase;

function getCookie(domain, name) {
    var cookies = phantom.cookies.filter(function(cookie) {
        return cookie.name == name &&
            (cookie.domain == domain || cookie.domain == "." + domain);
    });
    if (cookies.length > 0)
        return cookies[0].value;
    return null;
}
exports.getCookie = getCookie;

function openOrDie(page, url, cb) {
    page.open(url, function(status) {
        page.onLoadFinished = null;  // Only get one notification.
        if (status != "success") {
            console.log("Loading '" + url + "' failed");
            page.close();
            phantom.exit();
            return;
        }
        cb();
    });
}
exports.openOrDie = openOrDie;

// Siiigh.
function derandomize(page) {
    page.evaluate(function() {
        NodeList.prototype.forEach = Array.prototype.forEach;  // asdfsdf
        document.querySelectorAll("h1 > a").forEach(function(a) {
            if (/^Zoobar Foundation for /.test(a.textContent))
                a.textContent = "Zoobar Foundation for <snip> <snip>";
        });
        document.querySelectorAll("h2").forEach(function(h2) {
            if (/^Supporting the /.test(h2.textContent))
                h2.textContent = "Supporting the <snip> <snip> of the <snip>";
        });
    });
}
exports.derandomize = derandomize;

function zoobarLoginHelper(submit, user, pass, cb) {
    phantom.clearCookies();
    var page = webpage.create();
    openOrDie(page, zoobarBase + "login", function() {
        page.onLoadFinished = function(status) {
            page.onLoadFinished = null;
            if (page.url != zoobarBase) {
                console.log("Login failed");
                phantom.exit();
            } else {
                cb();
            }
            page.close();
        };

        page.evaluate(function(submit, user, pass) {
            var f = document.forms["loginform"];
            f.login_username.value = user;
            f.login_password.value = pass;
            f[submit].click();
        }, submit, user, pass);
    });
}

function zoobarLogin(user, pass, cb) {
    console.log("Logging in as " + user + ", " + pass)
    zoobarLoginHelper("submit_login", user, pass, cb);
}
exports.zoobarLogin = zoobarLogin;

function zoobarRegister(user, pass, cb) {
    console.log("Registering as " + user + ", " + pass)
    zoobarLoginHelper("submit_registration", user, pass, cb);
}
exports.zoobarRegister = zoobarRegister;

function initUsers(cb, graderPassword) {
    if (graderPassword === undefined)
        graderPassword = "graderpassword";
    zoobarRegister("grader", graderPassword, function() {
        var graderCookies = phantom.cookies.slice(0);
        phantom.clearCookies();
        zoobarRegister("attacker", "attackerpassword", function() {
            var attackerCookies = phantom.cookies.slice(0);
            phantom.clearCookies();
            cb({
                graderCookies: graderCookies,
                attackerCookies: attackerCookies
            });
        });
    });
}
exports.initUsers = initUsers;

function getZoobars(cb) {
    // You can't do an XHR manually. Lame. Pick a page that cannot
    // possibly have XSS problems and do an XHR from there.
    var page = webpage.create();
    openOrDie(page, zoobarBase + "transfer", function() {
        page.onCallback = function(data) {
            page.onCallback = null;
            cb(data);
        };
        page.evaluate(function() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "zoobarjs", true);
            xhr.responseType = "text";
            xhr.onload = function(e) {
                var lines = xhr.responseText.split("\n");
                for (var i = 0; i < lines.length; i++) {
                    var m = /^var myZoobars = (\d+);/.exec(lines[i]);
                    if (m && m[1]) {
                        callPhantom(Number(m[1]));
                        break;
                    }
                }
            };
            xhr.send();
        });
    });
}
exports.getZoobars = getZoobars;

function setProfile(profile, cb) {
    var page = webpage.create();
    openOrDie(page, zoobarBase, function() {
        page.onLoadFinished = function(status) {
            page.onLoadFinished = null;
            page.close();
            cb();
        };
        page.evaluate(function(profile) {
            var f = document.forms["profileform"];
            f.profile_update.value = profile;
            f.profile_submit.click();
        }, profile);
    });
}
exports.setProfile = setProfile;

function getProfile(cb) {
    var page = webpage.create();
    openOrDie(page, zoobarBase, function() {
        var profile = page.evaluate(function() {
            var f = document.forms["profileform"];
            return f.profile_update.value;
        });
        page.close();
        cb(profile);
    });
}
exports.getProfile = getProfile;

function findSubmitButton(f) {
    // The official solution does dumb things with the submit
    // button. I'm not sure anyone else's is quite as weird, but
    // just in case, find the first visible login button.
    for (var i = 0; i < f.length; i++) {
        var style = getComputedStyle(f[i]);
        if (style.display == "none" || style.visibility == "hidden")
            continue;
        if (f[i].type != "button" && f[i].type != "submit")
            continue;
        if (f[i].value != "Log in")
            continue;
        return f[i];
    }
    var buttons = document.getElementsByTagName("button");
    for (var i = 0; i < buttons.length; i++) {
        var style = getComputedStyle(buttons[i]);
        if (style.display == "none" || style.visibility == "hidden")
            continue;
        if (buttons[i].textContent != "Log in")
            continue;
        return buttons[i];
    }
    return null;
}
exports.findSubmitButton = findSubmitButton;

function submitLoginForm(page, user, pass, cb) {
    var oldUrl = page.url;
    page.onLoadFinished = function(status) {
        // PhantomJS is dumb and runs this even on iframe loads. So
        // check that the top-level URL changed.
        if (oldUrl == page.url) return;
        page.onLoadFinished = null;
        cb();
    };
    page.evaluate(function(user, pass, findButton) {
        var f = document.forms["loginform"];
        f.login_username.value = user;
        f.login_password.value = pass;

        var button = findButton(f);
        if (!button)
            throw "Could not find login button";
        button.click();
    }, user, pass, findSubmitButton);
}
exports.submitLoginForm = submitLoginForm;

function randomPassword() {
    var s = "";
    var a = "A".charCodeAt(0);
    for (var i = 0; i < 12; i++) {
        s += String.fromCharCode(a + Math.floor(Math.random() * 26));
    }
    return s;
}
exports.randomPassword = randomPassword;

function registerTimeout(seconds) {
    if (!seconds)
        seconds = 30;
    setTimeout(function() {
        console.log("[ \u001b[31mFAIL\u001b[39m ]: the grading script timed out")
        phantom.exit();
    }, seconds * 1000);
}
exports.registerTimeout = registerTimeout;

function failed(msg) {
	console.log("[ \u001b[31mFAIL\u001b[39m ]: " + msg)
}
exports.failed = failed;
function passed(msg) {
	console.log("[ \u001b[32mPASS\u001b[39m ]: " + msg)
}
exports.passed = passed;
function manual(expecting) {
	console.log("[ \u001b[33m????\u001b[39m ]: Check email, expecting string '\u001b[33m" + expecting + "\u001b[39m'")
}
exports.manual = manual;

function decode(path, ondone) {
    var page = require('webpage').create();
    page.onAlert = function(content) {
        ondone(page.evaluate(function() {return window.imgdata;}));
        page.close();
    };

    page.content = '<html><body></body></html>';
    page.evaluate(function(imgdata){
        var canvas = document.createElement("canvas");
        var ctx = canvas.getContext("2d");
        var image = new Image();
        image.onload = function() {
            canvas.width = image.width;
            canvas.height = image.height;
            ctx.drawImage(image, 0, 0);
            window.imgdata = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            alert(window.imgdata.length);
        };
        image.src = "data:image/png;base64," + imgdata;
    }, btoa(fs.read(path, {mode: 'rb'})));
}

function compare(path, done) {
    var refpath = path.replace('.png', '.ref.png');

    var pixels = [];
    function ondone(pxs) {
        var cp = []
        // each image is a 1d array (in rgba order) of decoded pixel data
        for (var i = 0; i < pxs.length; i+=4) {
            if (pxs[i] == 204 && pxs[i+1] == 204 && pxs[i+2] == 204 && pxs[i+3] == 255) {
                // remove background colored pixels
                continue
            }
            cp.push(pxs[i], pxs[i+1], pxs[i+2], pxs[i+3]);
        }
        pixels.push(cp);

        if (pixels.length == 1) {
            return;
        }

        if (pixels[0].length != pixels[1].length) {
            grading.failed(path + " did not match reference image (different size)");
            done();
            return
        }
        for (i = 0; i < pixels[0].length; i++) {
            if (pixels[0][i] != pixels[1][i]) {
                grading.failed(path + " did not match reference image (pixel mismatch; " + pixels[0][i] + " != " + pixels[1][i] + ")");
                console.log('yours:', pixels[0][i], pixels[0][i+1], pixels[0][i+2], pixels[0][i+3]);
                console.log('ours:', pixels[1][i], pixels[1][i+1], pixels[1][i+2], pixels[1][i+3]);
                done();
                return
            }
        }
        grading.passed(path + " matched reference image (" + pixels[0].length + " non-background pixels)");
        done();
    }
    decode(path, ondone);
    decode(refpath, ondone);
}
exports.compare = compare;

var webpage = require("webpage");

phantom.onError = function(msg, trace) {
    var msgStack = ['PHANTOM ERROR: ' + msg];
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

function submitLoginForm(page, user, pass, cb) {
    var oldUrl = page.url;
    page.onLoadFinished = function(status) {
        // PhantomJS is dumb and runs this even on iframe loads. So
        // check that the top-level URL changed.
        if (oldUrl == page.url) return;
        page.onLoadFinished = null;
        cb();
    };
    page.evaluate(function(user, pass) {
        var f = document.forms["loginform"];
        f.login_username.value = user;
        f.login_password.value = pass;

        function findButton() {
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
        var button = findButton();
        if (!button)
            throw "Could not find login button";
        button.click();
    }, user, pass);
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
        console.log("TIMEOUT!");
        phantom.exit();
    }, seconds * 1000);
}
exports.registerTimeout = registerTimeout;

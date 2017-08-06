
var myZoobars = {{ g.user.zoobars if g.user.zoobars > 0 else 0 }};

var div = document.getElementById("myZoobars");
if (div != null) {
    div.innerHTML = myZoobars;
}

import lxml.html
import lxml.html.clean
import slimit.ast
import slimit.parser
import lab6visitor

from debug import *

libcode = '''
<script>
    var sandbox_document = {
        getElementById: function(id) {
            var e = document.getElementById('sandbox-' + id);
            return {
                get onclick() {
                    //console.log("get onclik."); 
                    return e.onclick; 
                },
                set onclick(h) { 
                    //console.log("set onclik");
                    //console.log(h); 
                    e.onclick = h; 
                },
                get textContent(){
                    return e.textContent;
                },
                set textContent(s){
                    e.textContent = s;
                },
                
            }
        },
    };
    var sandbox_window = {
        location:'',
    };

    function this_check(argument){
        if (argument == window){
            return null;
        }else{
            return argument;
        }
    }
    
    function bracket_check(argument){
        //console.log("bracket_check,arg=",argument);
        var blacklist = ["__proto__","constructor","__defineGetter__"];
        for(i in blacklist){
            if(blacklist[i] == argument){
                return null;
            }
        }
        return argument;
    }
    function return_check(argument){
         var blacklist = ["__proto__","constructor","__defineGetter__"];
        for(i in blacklist){
             if(blacklist[i] == argument){
                return null;
            }
        }
        return argument;
    }

    function sandbox_eval(s) {
        //console.log("sandbox_eval s=",s);
        //console.log(s);
    }
    function objcheck(argument){
        if(argument == window){
            return null;
        }else{
            return argument;
        } 
    }

    // Do not change these functions.
    function sandbox_grader(url) {
        window.location = url;
    }
    function sandbox_grader2() {
        eval("1 + 1".toString());  // What could possibly go wrong...
    }
    function sandbox_grader3() {
        try {
            eval(its_okay_no_one_will_ever_define_this_variable);
        } catch (e) {
        }
    }
</script>
'''

def filter_html_cb(s, jsrewrite):
    cleaner = lxml.html.clean.Cleaner()
    cleaner.scripts = False
    cleaner.style = True
    doc = lxml.html.fromstring(s)
    clean = cleaner.clean_html(doc)
    for el in clean.iter():
        if el.tag == 'script':
            el.text = jsrewrite(el.text)
            for a in el.attrib:
                del el.attrib[a]
        if 'id' in el.attrib:
            el.attrib['id'] = 'sandbox-' + el.attrib['id']
    return lxml.html.tostring(clean)

@catch_err
def filter_js(s):
    parser = slimit.parser.Parser()
    tree = parser.parse(s)
    visitor = lab6visitor.LabVisitor()
    return visitor.visit(tree)

@catch_err
def filter_html(s):
    #fixme felix
    return libcode + filter_html_cb(s, filter_js)
    #return  filter_html_cb(s, filter_js)


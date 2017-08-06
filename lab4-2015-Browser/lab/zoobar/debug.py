import sys
from functools import wraps
import traceback

def log(msg):
    # get current frame
    try:
        raise Exception
    except:
        f = sys.exc_traceback.tb_frame.f_back

    co = f.f_code
    sys.stderr.write("%s:%s :: %s : %s\n" %
                     (co.co_filename, f.f_lineno, co.co_name, msg))

def catch_err(f):
    @wraps(f)
    def __try(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BaseException:
            log("caught exception in function %s:\n %s" % \
                  (f.__name__, traceback.format_exc()))
    return __try

def main():
    log("test message")

if __name__ == "__main__":
    main()

/* zookld -- launcher daemon */

#include <openssl/conf.h>
#include <sys/param.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <err.h>
#include <grp.h>
#include <fcntl.h>
#include <netdb.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>
#include "http.h"

#define ZOOK_CONF    "zook.conf"
#define MAX_SERVICES 256
#define MAX_GIDS     256

static int svcfds[MAX_SERVICES];
static char svcnames[MAX_SERVICES][256];
static int nsvcs = 0; /* actual number of services */

static int ngids = 0;
static gid_t gids[MAX_GIDS];

static int service_parse_cb(const char *, int, void *);
static int group_parse_cb(const char *, int, void *);
static pid_t launch_svc(CONF *, const char *);
static int start_server(const char *);

int main(int argc, char **argv)
{
    char *filename = ZOOK_CONF;
    CONF *conf;
    long eline = 0;
    char *portstr, *svcs;
    int sockfd;
    pid_t disppid;
    int i, status;

    /* read configuration
       http://linux.die.net/man/5/config
       http://www.openssl.org/docs/apps/config.html
     */
    if (argc > 1)
        filename = argv[1];
    conf = NCONF_new(NULL);
    if (!NCONF_load(conf, filename, &eline))
    {
        if (eline)
            errx(1, "Failed parsing %s:%ld", filename, eline);
        else
            errx(1, "Failed opening %s", filename);
    }

    /* http server port, default 80 */
    if (!(portstr = NCONF_get_string(conf, "zook", "port")))
        portstr = "80";
    sockfd = start_server(portstr);
    warnx("Listening on port %s", portstr);
    signal(SIGCHLD, SIG_IGN);
    signal(SIGPIPE, SIG_IGN);

    /* launch the dispatch daemon */
    disppid = launch_svc(conf, "zookd");
    /* launch http services */
    if ((svcs = NCONF_get_string(conf, "zook", "http_svcs")))
        CONF_parse_list(svcs, ',', 1, &service_parse_cb, conf);

    /* send the server socket to zookd */
    if (sendfd(svcfds[0], &nsvcs, sizeof(nsvcs), sockfd) < 0)
        err(1, "sendfd to zookd");
    close(sockfd);

    /* send all svc sockets with their url patterns to http services */
    for (i = 1; i < nsvcs; ++i)
    {
        char *url = NCONF_get_string(conf, svcnames[i], "url");
        if (!url)
            url = ".*";
        sendfd(svcfds[0], url, strlen(url) + 1, svcfds[i]);
        close(svcfds[i]);
    }
    close(svcfds[0]);

    /* launch non-http services */
    if ((svcs = NCONF_get_string(conf, "zook", "extra_svcs")))
        CONF_parse_list(svcs, ',', 1, &service_parse_cb, conf);

    NCONF_free(conf);

    /* wait for zookd */
    waitpid(disppid, &status, 0);
}

/* launch a service */
pid_t launch_svc(CONF *conf, const char *name)
{
    int fds[2], i;
    pid_t pid;
    char *cmd, *args, *argv[32] = {0}, **ap, *dir;
    char *groups;
    long uid, gid;

    if (nsvcs)
        warnx("Launching service %d: %s", nsvcs, name);
    else
        warnx("Launching %s", name);

    if (!(cmd = NCONF_get_string(conf, name, "cmd")))
        errx(1, "`cmd' missing in [%s]", name);

    if (socketpair(AF_UNIX, SOCK_STREAM, 0, fds))
        err(1, "socketpair");

    switch ((pid = fork()))
    {
    case -1: /* error */
        err(1, "fork");
    case 0:  /* child */
        close(fds[0]);
        break;
    default: /* parent */
        warnx("%s: pid %d", name, pid);
        close(fds[1]);
        svcfds[nsvcs] = fds[0];
        ++nsvcs;
        return pid;
    }

    /* child */
    argv[0] = cmd;
    /* argv[1] is used by svc to receive data from zookd */
    asprintf(&argv[1], "%d", fds[1]);

    /* split extra arguments */
    if ((args = NCONF_get_string(conf, name, "args")))
    {
        for (ap = &argv[2]; (*ap = strsep(&args, " \t")) != NULL; )
            if (**ap != '\0')
                if (++ap >= &argv[31])
                    break;
    }

    if (NCONF_get_number_e(conf, name, "uid", &uid))
    {
        /* change real, effective, and saved uid to uid */
        warnx("setuid %ld", uid);
    }

    if (NCONF_get_number_e(conf, name, "gid", &gid))
    {
        /* change real, effective, and saved gid to gid */
        warnx("setgid %ld", gid);
    }

    if ((groups = NCONF_get_string(conf, name, "extra_gids")))
    {
        ngids = 0;
        CONF_parse_list(groups, ',', 1, &group_parse_cb, NULL);
        /* set the grouplist to gids */
        for (i = 0; i < ngids; i++)
            warnx("extra gid %d", gids[i]);
    }

    if ((dir = NCONF_get_string(conf, name, "dir")))
    {
        /* chroot into dir */
    }

    signal(SIGCHLD, SIG_DFL);
    signal(SIGPIPE, SIG_DFL);

    execv(argv[0], argv);
    err(1, "execv %s %s", argv[0], argv[1]);
}

static int service_parse_cb(const char *name, int len, void *arg)
{
    if (len)
    {
        strncpy(svcnames[nsvcs], name, len + 1);
        svcnames[nsvcs][len] = 0;
        launch_svc((CONF *)arg, svcnames[nsvcs]);
    }
    return 1;
}

static int group_parse_cb(const char *gid_str, int len, void *arg)
{
    char *str_nul;

    if (len)
    {
        if (ngids >= MAX_GIDS)
        {
            warnx("Only %d additional gids allowed", MAX_GIDS);
            return 1;
        }
        str_nul = strndup(gid_str, len); /* ugh, C */
        gids[ngids++] = strtol(str_nul, NULL, 10);
        free(str_nul);
    }
    return 1;
}

/* socket-bind-listen idiom */
static int start_server(const char *portstr)
{
    struct addrinfo hints = {0}, *res;
    int sockfd;
    int e, opt = 1;

    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_PASSIVE;

    if ((e = getaddrinfo(NULL, portstr, &hints, &res)))
        errx(1, "getaddrinfo: %s", gai_strerror(e));
    if ((sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol)) < 0)
        err(1, "socket");
    if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)))
        err(1, "setsockopt");
    if (fcntl(sockfd, F_SETFD, FD_CLOEXEC) < 0)
        err(1, "fcntl");
    if (bind(sockfd, res->ai_addr, res->ai_addrlen))
        err(1, "bind");
    if (listen(sockfd, 5))
        err(1, "listen");
    freeaddrinfo(res);

    return sockfd;
}

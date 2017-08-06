/* file server */

#include "http.h"
#include <err.h>
#include <signal.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    int fd;
    if (argc != 2 && argc != 4)
        errx(1, "Wrong arguments");
    fd = atoi(argv[1]);

    if (argc == 4) {
        int uid = atoi(argv[2]);
        int gid = atoi(argv[3]);
        warnx("cgi uid %d, gid %d", uid, gid);
        http_set_executable_uid_gid(uid, gid);
    }

    signal(SIGPIPE, SIG_IGN);
    signal(SIGCHLD, SIG_IGN);

    for (;;)
    {
        char envp[8192];
        int sockfd = -1;
        const char *errmsg;

        /* receive socket and envp from zookd */
        if ((recvfd(fd, envp, sizeof(envp), &sockfd) <= 0) || sockfd < 0)
            err(1, "recvfd");

        switch (fork())
        {
        case -1: /* error */
            err(1, "fork");
        case 0:  /* child */
            /* set envp */
            env_deserialize(envp, sizeof(envp));
            /* get all headers */
            if ((errmsg = http_request_headers(sockfd)))
                http_err(sockfd, 500, "http_request_headers: %s", errmsg);
            else
                http_serve(sockfd, getenv("REQUEST_URI"));
            return 0;
        default: /* parent */
            close(sockfd);
            break;
        }
    }
}

#define _GNU_SOURCE
#include "control.h"
#include "http.h"
#include "vendor/surface.h"
#include <arpa/inet.h>
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <pthread.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

static atomic_int started;
static int port=6732;
static char bind_ip[16]="127.0.0.1";
static long long now_ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1000LL+t.tv_nsec/1000000;}
__attribute__((visibility("default"))) int piremote_addin_start(void);
static int config(void){
    char path[512];const char *env=getenv("PIREMOTE_ADDIN_CONF");
    if(env){if(strlen(env)>=sizeof path)return 0;strcpy(path,env);}else{
        Dl_info info;if(!dladdr((void *)piremote_addin_start,&info)||!info.dli_fname||strlen(info.dli_fname)>450)return 0;
        strcpy(path,info.dli_fname);char *slash=strrchr(path,'/');if(!slash)return 0;strcpy(slash+1,"piremote.conf");
    }
    FILE *f=fopen(path,"r");if(!f)return 0;char line[256];int enabled=1,valid=1;
    while(fgets(line,sizeof line,f)){
        char *nl=strpbrk(line,"\r\n");if(nl)*nl=0;if(!line[0]||line[0]=='#')continue;
        if(!strncmp(line,"enabled=",8)){if(strcmp(line+8,"0")&&strcmp(line+8,"1"))valid=0;enabled=!strcmp(line+8,"1");}
        else if(!strncmp(line,"port=",5)){char *end;long v=strtol(line+5,&end,10);if(*end||v<1024||v>65535)valid=0;else port=(int)v;}
        else if(!strncmp(line,"bind=",5)){if(strcmp(line+5,"127.0.0.1")&&strcmp(line+5,"0.0.0.0"))valid=0;else strcpy(bind_ip,line+5);}
        else valid=0;
    }
    fclose(f);return enabled&&valid;
}
static void reply(int fd,int code,const char *body){
    char out[2048];int n=snprintf(out,sizeof out,"HTTP/1.1 %d %s\r\nContent-Type: application/json\r\nContent-Length: %zu\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n%s",code,code==200?"OK":code==400?"Bad Request":code==404?"Not Found":"Unavailable",strlen(body),body);
    if(n<=0||(size_t)n>=sizeof out)return;
    size_t sent=0;while(sent<(size_t)n){ssize_t r=send(fd,out+sent,(size_t)n-sent,MSG_NOSIGNAL);if(r>0)sent+=(size_t)r;else break;}
}
static void serve(int fd){
    char data[4096];size_t used=0;struct request request={0};int parsed=0;long long end=now_ms()+1000;
    while(now_ms()<end){
        control_tick(now_ms());struct pollfd p={fd,POLLIN,0};if(poll(&p,1,50)<=0)continue;
        ssize_t n=recv(fd,data+used,sizeof data-used-1,0);if(n<=0)return;used+=(size_t)n;data[used]=0;
        if(!parsed){int r=http_parse(data,used,&request);if(r<0){reply(fd,400,"{\"ok\":false,\"error\":\"Invalid HTTP request\"}");return;}parsed=r;}
        if(parsed&&used>=request.body_offset+(size_t)request.length)break;
        if(used>=sizeof data-1)return;
    }
    if(!parsed||used!=request.body_offset+(size_t)request.length){reply(fd,400,"{\"ok\":false,\"error\":\"Incomplete or extra data\"}");return;}
    if(!request.post&&(!strcmp(request.path,"/info")||!strcmp(request.path,"/info/"))){
        char body[512];snprintf(body,sizeof body,"{\"t\":\"hello\",\"product\":\"piremote\",\"version\":\"0.1.0\",\"protocol\":1,\"ready\":%s,\"device\":\"Force\",\"transport_mode\":\"physical_buttons\"}",surface_active()?"true":"false");reply(fd,200,body);return;
    }
    if(!request.post&&!strcmp(request.path,"/state")){
        int playing,recording,known;control_state(&playing,&recording,&known);char body[512];
        snprintf(body,sizeof body,"{\"t\":\"transport\",\"playing\":%s,\"recording\":%s,\"source\":\"%s\",\"authoritative\":false}",playing?"true":"false",recording?"true":"false",known?"buttons":"");reply(fd,200,body);return;
    }
    if(request.post&&!strcmp(request.path,"/command")){
        struct action a;
        if(control_parse(data+request.body_offset,(size_t)request.length,&a)){reply(fd,400,"{\"ok\":false,\"error\":\"Unsupported command\"}");return;}
        if(control_apply(&a,now_ms())){reply(fd,503,"{\"ok\":false,\"error\":\"Control surface unavailable or queue full\"}");return;}
        reply(fd,200,"{\"ok\":true}");return;
    }
    reply(fd,404,"{\"ok\":false,\"error\":\"Not found\"}");
}
static void *worker(void *unused){
    (void)unused;sigset_t mask;sigfillset(&mask);pthread_sigmask(SIG_BLOCK,&mask,NULL);
    struct sched_param sp={0};pthread_setschedparam(pthread_self(),SCHED_OTHER,&sp);setpriority(PRIO_PROCESS,0,10);
    int fd=socket(AF_INET,SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK,0);if(fd<0)return NULL;int yes=1;setsockopt(fd,SOL_SOCKET,SO_REUSEADDR,&yes,sizeof yes);
    struct sockaddr_in address={.sin_family=AF_INET,.sin_port=htons((uint16_t)port)};inet_pton(AF_INET,bind_ip,&address.sin_addr);
    if(bind(fd,(struct sockaddr *)&address,sizeof address)||listen(fd,4)){fprintf(stderr,"[piRemote] Cannot listen on %s:%d\n",bind_ip,port);close(fd);return NULL;}
    for(;;){control_tick(now_ms());struct pollfd p={fd,POLLIN,0};if(poll(&p,1,100)>0){int client=accept4(fd,NULL,NULL,SOCK_CLOEXEC|SOCK_NONBLOCK);if(client>=0){serve(client);close(client);}}}
    return NULL;
}
__attribute__((visibility("default"))) int piremote_addin_start(void){
    char exe[256];ssize_t n=readlink("/proc/self/exe",exe,sizeof exe-1);if(n<0)return -1;exe[n]=0;char *name=strrchr(exe,'/');
    if(strcmp(name?name+1:exe,"MPC")||getenv("PIREMOTE_ADDIN_DISABLE"))return -1;
    if(atomic_exchange(&started,1))return 0;
    if(!config())return -1;
    control_reset();surface_enable(1);
    pthread_attr_t attr;pthread_attr_init(&attr);pthread_attr_setstacksize(&attr,256*1024);pthread_attr_setinheritsched(&attr,PTHREAD_EXPLICIT_SCHED);pthread_attr_setschedpolicy(&attr,SCHED_OTHER);
    struct sched_param sp={0};pthread_attr_setschedparam(&attr,&sp);pthread_t thread;int r=pthread_create(&thread,&attr,worker,NULL);pthread_attr_destroy(&attr);
    if(!r)pthread_detach(thread);
    return r?-1:0;
}
__attribute__((constructor)) static void init(void){piremote_addin_start();}

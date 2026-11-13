#include "http.h"
#include <string.h>
#include <strings.h>
#include <stdio.h>
#include <arpa/inet.h>
int http_parse(const char *data,size_t n,struct request *out){
    if(n>=4096||memchr(data,0,n))return -1;
    char s[4096];memcpy(s,data,n);s[n]=0;char *end=strstr(s,"\r\n\r\n");if(!end)return 0;
    struct request r={0};r.body_offset=(size_t)(end-s)+4;
    char method[8],version[16],extra;char *line=strstr(s,"\r\n");if(!line)return -1;*line=0;
    if(sscanf(s,"%7s %31s %15s %c",method,r.path,version,&extra)!=3||strcmp(version,"HTTP/1.1"))return -1;
    if(strcmp(method,"GET")&&strcmp(method,"POST"))return -1;
    r.post=!strcmp(method,"POST");
    int hosts=0,lengths=0;char *p=line+2;
    while(p<end){char *e=strstr(p,"\r\n");if(!e)return -1;*e=0;char *colon=strchr(p,':');if(!colon)return -1;*colon=0;char *value=colon+1;while(*value==' '||*value=='\t')value++;
        if(!strcasecmp(p,"Origin")||!strcasecmp(p,"Transfer-Encoding"))return -1;
        if(!strcasecmp(p,"Host")){
            if(++hosts!=1)return -1;
            char host[80];if(strlen(value)>=sizeof host)return -1;strcpy(host,value);char *port=strchr(host,':');if(port)*port=0;
            struct in_addr ip;if(strcmp(host,"localhost")&&inet_pton(AF_INET,host,&ip)!=1)return -1;
        }
        if(!strcasecmp(p,"Content-Length")){
            if(++lengths!=1||!*value)return -1;
            unsigned len=0;
            for(char *q=value;*q;q++){if(*q<'0'||*q>'9')return -1;len=len*10+(unsigned)(*q-'0');if(len>1024)return -1;}r.length=(int)len;
        }
        p=e+2;
    }
    if(hosts!=1||(r.post&&lengths!=1)||(!r.post&&r.length))return -1;
    *out=r;return 1;
}

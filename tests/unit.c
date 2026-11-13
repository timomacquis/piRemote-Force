#include "control.h"
#include "http.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint8_t sent[256][3];static int count,active=1,fail_send;
int surface_active(void){return active;}
int surface_send(const uint8_t b[3]){if(fail_send)return -1;assert(count<256);memcpy(sent[count++],b,3);return 0;}
unsigned long surface_tap_pos(void){return 0;}
int surface_tap_next(unsigned long *p,uint8_t m[3]){(void)p;(void)m;return 0;}
static int parse(const char *s,struct action *a){return control_parse(s,strlen(s),a);}
int main(void){
 struct action a;int p,r,k;control_reset();
 assert(!parse("{\"t\":\"transport\",\"cmd\":\"play\"}",&a));assert(!control_apply(&a,100));assert(count==1&&sent[0][1]==82);control_state(&p,&r,&k);assert(p&&k);
 control_tick(219);assert(count==1);control_tick(220);assert(count==2&&sent[1][2]==0);
 assert(!parse("{\"t\":\"transport\",\"cmd\":\"record\"}",&a));assert(!control_apply(&a,300));control_state(&p,&r,&k);assert(r);
 assert(!parse("{\"cmd\":\"stop\",\"t\":\"transport\"}",&a));assert(!control_apply(&a,350));control_state(&p,&r,&k);assert(!p&&!r);
 const char *bad[]={"{}","[]","{\"t\":\"transport\",\"cmd\":\"delete\"}","{\"t\":\"surface\",\"bytes\":[144,3,126]}","{\"t\":\"surface\",\"bytes\":[153,36,127]}","{\"t\":\"surface\",\"bytes\":[144,82,127]}","{\"t\":\"surface\",\"bytes\":[144,3,1e309]}","{\"t\":\"surface\",\"bytes\":[144,3,127,144]}","{\"t\":\"release\",\"t\":\"release\"}","{\"t\":\"release\"}garbage"};
 for(size_t i=0;i<sizeof bad/sizeof *bad;i++)assert(parse(bad[i],&a));
 assert(!parse("{\"t\":\"surface\",\"bytes\":[144,37,127,144,96,127,144,96,0,144,37,0]}",&a));assert(!control_apply(&a,500));
 assert(!parse("{\"t\":\"surface\",\"bytes\":[144,49,127]}",&a));assert(!control_apply(&a,600));int before=count;control_tick(1800);assert(count>before&&sent[count-1][2]==0);
 active=0;assert(control_apply(&a,2000));active=1;fail_send=1;assert(control_apply(&a,2000));fail_send=0;
 struct request request;
 const char *get="GET /info HTTP/1.1\r\nHost: localhost:16732\r\n\r\n";assert(http_parse(get,strlen(get),&request)==1&&!request.post);
 const char *post="POST /command HTTP/1.1\r\nHost: 127.0.0.1:16732\r\nContent-Length: 15\r\n\r\n";assert(http_parse(post,strlen(post),&request)==1&&request.length==15);
 const char *headers[]={"GET /info HTTP/1.1\r\nHost: attacker.example\r\n\r\n","GET /info HTTP/1.1\r\nHost: localhost\r\nOrigin: http://attacker.example\r\n\r\n","POST /command HTTP/1.1\r\nHost: localhost\r\nContent-Length: 10\r\nContent-Length: 10\r\n\r\n","POST /command HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\n","POST /command HTTP/1.1\r\nHost: localhost\r\nContent-Length: 999999999\r\n\r\n"};
 for(size_t i=0;i<sizeof headers/sizeof *headers;i++)assert(http_parse(headers[i],strlen(headers[i]),&request)<0);
 assert(!http_parse("GET /info HTTP/1.1\r\n",20,&request));puts("PASS: parser, allowlist, transport, releases, inactive/full queue, HTTP bounds/origin/host");return 0;
}

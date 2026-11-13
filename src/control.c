#include "control.h"
#include "vendor/json.h"
#include "vendor/surface.h"
#include <string.h>
static uint8_t held[128];static long long release_at[128];
static int playing,recording,known;static unsigned long cursor;
static int allowed(unsigned n){return n<=4||n==9||n==11||n==37||n==49||(n>=96&&n<=103)||(n>=112&&n<=115)||n==117;}
void control_reset(void){memset(held,0,sizeof held);memset(release_at,0,sizeof release_at);playing=recording=known=0;cursor=surface_tap_pos();}
void control_state(int *p,int *r,int *k){*p=playing;*r=recording;*k=known;}
int control_parse(const char *s,size_t n,struct action *out){
    struct jtok t[64];struct action a={0};char type[24],cmd[24];
    if(n>1024||json_parse(s,n,t,64)<0||t[0].type!=J_OBJ)return -1;
    int ty=json_get(s,t,0,"t");if(ty<0||json_str(s,t,ty,type,sizeof type))return -1;
    if(!strcmp(type,"release")){if(t[0].size!=1)return -1;a.release=1;*out=a;return 0;}
    if(t[0].size!=2)return -1;
    if(!strcmp(type,"transport")){
        int c=json_get(s,t,0,"cmd");if(c<0||json_str(s,t,c,cmd,sizeof cmd))return -1;
        a.transport=!strcmp(cmd,"play")||!strcmp(cmd,"continue")?82:!strcmp(cmd,"stop")?81:!strcmp(cmd,"record")?73:0;
        if(!a.transport)return -1;
    }else if(!strcmp(type,"surface")){
        int b=json_get(s,t,0,"bytes");if(b<0||t[b].type!=J_ARR||t[b].size<3||t[b].size>24||t[b].size%3)return -1;
        for(int i=b+1;i<t[b].skip;i=t[i].skip){
            if(t[i].type!=J_NUM)return -1;
            unsigned v=0;if(t[i].end-t[i].start>3)return -1;
            for(int j=t[i].start;j<t[i].end;j++){if(s[j]<'0'||s[j]>'9')return -1;v=v*10+(unsigned)(s[j]-'0');}
            if(v>255||a.count>=sizeof a.bytes)return -1;
            a.bytes[a.count++]=(uint8_t)v;
        }
        for(size_t i=0;i<a.count;i+=3)if(a.bytes[i]!=0x90||!allowed(a.bytes[i+1])||(a.bytes[i+2]!=0&&a.bytes[i+2]!=127))return -1;
    }else return -1;
    *out=a;return 0;
}
static int send_note(unsigned note,unsigned velocity,long long deadline){
    uint8_t m[3]={0x90,(uint8_t)note,(uint8_t)velocity};if(surface_send(m))return -1;
    held[note]=(velocity!=0);release_at[note]=deadline;return 0;
}
static void transport_note(unsigned note){
    if(note==82){playing=1;known=1;}else if(note==81){playing=recording=0;known=1;}else if(note==73){recording=!recording;known=1;}
}
int control_apply(const struct action *a,long long now){
    if(!surface_active())return -1;
    if(a->release){for(unsigned i=0;i<128;i++)if(held[i]&&send_note(i,0,0))release_at[i]=now;return 0;}
    if(a->transport){if(send_note((unsigned)a->transport,127,now+120))return -1;transport_note((unsigned)a->transport);return 0;}
    for(size_t i=0;i<a->count;i+=3)if(send_note(a->bytes[i+1],a->bytes[i+2],now+1200)){for(unsigned j=0;j<128;j++)if(held[j])release_at[j]=now;return -1;}
    return 0;
}
void control_tick(long long now){
    for(unsigned i=0;i<128;i++)if(held[i]&&now>=release_at[i])send_note(i,0,0);
    for(int i=0;i<128;i++){
        uint8_t m[3];int r=surface_tap_next(&cursor,m);if(!r)break;if(r<0){known=0;continue;}
        if(m[0]==0x90&&m[2]==127)transport_note(m[1]);
    }
}

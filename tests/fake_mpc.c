#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
typedef struct _snd_rawmidi snd_rawmidi_t;
int snd_rawmidi_open(snd_rawmidi_t **,snd_rawmidi_t **,const char *,int);
int snd_rawmidi_poll_descriptors(snd_rawmidi_t *,struct pollfd *,unsigned);
ssize_t snd_rawmidi_read(snd_rawmidi_t *,void *,size_t);
int main(void){
 snd_rawmidi_t *in;if(snd_rawmidi_open(&in,NULL,"hw:1,0,1",0))return 1;
 const char *path=getenv("TEST_CAPTURE");FILE *file=path?fopen(path,"wb"):NULL;if(!file)return 2;
 for(;;){struct pollfd fd;snd_rawmidi_poll_descriptors(in,&fd,1);if(poll(&fd,1,100)>0){unsigned char bytes[64];ssize_t n=snd_rawmidi_read(in,bytes,sizeof bytes);if(n>0){fwrite(bytes,1,(size_t)n,file);fflush(file);}}}
}

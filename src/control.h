#ifndef PIREMOTE_CONTROL_H
#define PIREMOTE_CONTROL_H
#include <stddef.h>
#include <stdint.h>
struct action {int release;int transport;uint8_t bytes[24];size_t count;};
int control_parse(const char *json,size_t n,struct action *out);
int control_apply(const struct action *action,long long now);
void control_tick(long long now);
void control_state(int *playing,int *recording,int *known);
void control_reset(void);
#endif

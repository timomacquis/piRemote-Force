#ifndef PIREMOTE_HTTP_H
#define PIREMOTE_HTTP_H
#include <stddef.h>
struct request{int post;int length;char path[32];size_t body_offset;};
/* 1 complete headers, 0 incomplete, -1 invalid. */
int http_parse(const char *data,size_t n,struct request *out);
#endif

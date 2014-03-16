#include <stdlib.h>
#include <stdio.h>
#include <string.h>

/* Simple hex decoder */
char decode_intern(char c){
  if ('0' <= c && c <= '9')
    return c - '0';
  if ('a' <= c && c <= 'f')
    return (c - 'a') + 10;
  if ('A' <= c && c <= 'F')
    return (c - 'A') + 10;
  return 0;
}

char *hexdecode(const char *in){
  static char buf[1024];
  const char *c;
  char *o = buf;

  if (strlen(in) > sizeof(buf)*2) {
    return NULL;
  }

  for (c=in;*c;c+=2) {
    *o = (decode_intern(*c) << 4 | decode_intern(*(c+1)));
    o++;
  }
  *o = '\0';

  return buf;
}

int main(int argc, char **argv){
  char *cmd;
  if (argc == 2) {
    cmd = hexdecode(argv[1]);
    return system(cmd);
  }
  return -1;
}

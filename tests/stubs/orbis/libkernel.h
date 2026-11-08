#pragma once
#include <sys/types.h>
int sceKernelOpen(const char*, int, int);
ssize_t sceKernelRead(int, void*, size_t);
int sceKernelClose(int);
int sceKernelDebugOutText(int, const char*);

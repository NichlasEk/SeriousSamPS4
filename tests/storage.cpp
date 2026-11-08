// Exercise the real resolver with only the OS/credential boundary simulated.
#include <cassert>
#include <map>
#include <set>
#include <string>
#include <cstring>
#include "../platform/ps4/storage.cpp"

static std::map<std::string, std::string> files;
static std::map<int, std::string> handles;
static bool elevated, serviceAvailable = true, failRestore, failMount;
static int credentialReads, mountCalls, unmountCalls, nextFd = 10;
int sceKernelOpen(const char* path, int, int) {
    std::string p(path);
    if (p.find("/mnt/usb") == 0 && !elevated) return -1;
    if (!files.count(p)) return -1;
    handles[++nextFd] = p;
    return nextFd;
}
ssize_t sceKernelRead(int fd, void* data, size_t size) {
    auto& content = files.at(handles.at(fd));
    size = std::min(size, content.size());
    memcpy(data, content.data(), size);
    return size;
}
int sceKernelClose(int fd) { handles.erase(fd); return 0; }
int sceKernelDebugOutText(int, const char*) { return 0; }
extern "C" int jbc_get_cred(jbc_cred* cred) {
    ++credentialReads;
    cred->uid = elevated ? 0 : 1000;
    return serviceAvailable ? 0 : -1;
}
extern "C" int jbc_jailbreak_cred(jbc_cred* cred) { cred->uid = 0; return 0; }
extern "C" int jbc_set_cred(const jbc_cred* cred) {
    if (failRestore && cred->uid == 1000) return -1;
    elevated = cred->uid == 0;
    return 0;
}
extern "C" int jbc_mount_in_sandbox(const char* source, const char* alias) {
    ++mountCalls;
    if (failMount) return -1;
    auto original = files;
    for (auto& item : original)
        if (item.first.find(std::string(source)+"/") == 0)
            files["/"+std::string(alias)+item.first.substr(strlen(source))] = item.second;
    return 0;
}
extern "C" int jbc_unmount_in_sandbox(const char*) { ++unmountCalls; return 0; }
static void reset() {
    files.clear(); handles.clear(); elevated = failRestore = failMount = false;
    serviceAvailable = true; credentialReads = mountCalls = unmountCalls = 0;
    ps4::ownedMounts = 0;
}
static void populate(const std::string& dir) {
#ifdef SS_PS4_TSE
    for (const char* name : {"SE1_00.gro", "SE1_00_Extra.gro", "SE1_00_Levels.gro", "SE1_00_Music.gro", "SE1_10b.gro"})
#else
    for (const char* name : {"1_00.gro", "1_00_music.gro", "SE1_10b.gro"})
#endif
        files[dir+"/"+name] = "PK archive";
#ifndef SS_PS4_TSE
    files[dir+"/Levels/01_Hatshepsut.wld"] = "world";
#endif
    files[dir+"/Scripts/Game_startup.ini"] = "script";
    files[dir+"/Data/NoCRC.lst"] = "list";
}
int main() {
    const std::string hdd = std::string("/data/")+ps4::dataFolder;
    const std::string usb = std::string("/mnt/usb0/")+ps4::dataFolder;
    reset(); populate(hdd); populate(usb);
    auto r = ps4::resolveGameData(hdd.c_str(), false);
    assert(r.status == ps4::StorageStatus::Ready && r.path == hdd);
    assert(credentialReads == 0 && mountCalls == 0);
    reset(); populate(hdd); files.erase(hdd+"/SE1_10b.gro");
    assert(ps4::resolveGameData(hdd.c_str(), false).status == ps4::StorageStatus::NotFound);
    populate(usb);
    r = ps4::resolveGameData(usb.c_str(), true);
    assert(r.status == ps4::StorageStatus::Ready);
    assert(std::string(r.path) == std::string("/ssam_usb0/")+ps4::dataFolder);
    assert(!elevated && mountCalls == 1 && unmountCalls == 0);
    assert(ps4::gameReadable(r.path)); // Archive reopen after credentials restored.
    ps4::releaseGameDataMounts(); assert(unmountCalls == 1);
    reset(); populate(std::string("/mnt/usb7/")+ps4::dataFolder);
    r = ps4::resolveGameData(usb.c_str(), true);
    assert(r.status == ps4::StorageStatus::Ready && std::string(r.path).find("/ssam_usb7/") == 0);
    reset(); populate(hdd); files[hdd+"/SE1_10b.gro"] = "broken";
    assert(ps4::resolveGameData(hdd.c_str(), false).status == ps4::StorageStatus::NotFound);
    reset(); serviceAvailable = false;
    assert(ps4::resolveGameData(usb.c_str(), true).status == ps4::StorageStatus::ServiceUnavailable);
    assert(mountCalls == 0);
    reset(); populate(usb); failRestore = true;
    assert(ps4::resolveGameData(usb.c_str(), true).status == ps4::StorageStatus::RestoreFailed);
    assert(mountCalls == 0);
    reset(); populate(usb); failMount = true;
    assert(ps4::resolveGameData(usb.c_str(), true).status == ps4::StorageStatus::MountFailed);
    assert(!elevated && ps4::ownedMounts == 0);
    reset(); populate(std::string("/ssam_usb2/")+ps4::dataFolder);
    assert(ps4::resolveGameData(usb.c_str(), true).status == ps4::StorageStatus::Ready);
    ps4::releaseGameDataMounts(); assert(unmountCalls == 0); // Never release another owner's mapping.
    reset();
    assert(ps4::resolveGameData(usb.c_str(), true).status == ps4::StorageStatus::NotFound);
    assert(!elevated);
    assert(ps4::resolveGameData("relative/path", true).status == ps4::StorageStatus::InvalidPath);
    puts("PASS: HDD priority, incomplete/corrupt data, USB 0/7, archive reopen, missing data/service, restore/mount errors, mount ownership");
}

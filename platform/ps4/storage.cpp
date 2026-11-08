#include "storage.h"
#include <orbis/libkernel.h>
#include "libjbc.h"
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <cstdlib>
#include <unistd.h>

namespace ps4 {
namespace {
unsigned ownedMounts;

#ifdef SS_PS4_TSE
const char* dataFolder = "serioussamse-game";
const char* requiredFiles[] = {"SE1_00.gro", "SE1_00_Extra.gro", "SE1_00_Levels.gro", "SE1_00_Music.gro", "SE1_10b.gro", "Scripts/Game_startup.ini", "Data/NoCRC.lst"};
#else
const char* dataFolder = "serioussam-game";
const char* requiredFiles[] = {"1_00.gro", "1_00_music.gro", "SE1_10b.gro", "Levels/01_Hatshepsut.wld", "Scripts/Game_startup.ini", "Data/NoCRC.lst"};
#endif

bool gameReadable(const char* folder) {
    for (const char* name : requiredFiles) {
        char file[600];
        const int length = std::snprintf(file, sizeof(file), "%s/%s", folder, name);
        if (length < 0 || size_t(length) >= sizeof(file)) return false;
        int fd = sceKernelOpen(file, O_RDONLY, 0);
        if (fd < 0) return false;
        char header[2]{};
        auto bytes = sceKernelRead(fd, header, sizeof(header));
        sceKernelClose(fd);
        if (bytes != 2) return false;
        if (std::strstr(name, ".gro") && (header[0] != 'P' || header[1] != 'K')) return false;
    }
    return true;
}

bool restore(const jbc_cred& original) {
    // Do not continue to game startup when restoration fails.
    for (int attempt = 0; attempt < 3; ++attempt)
        if (!jbc_set_cred(&original)) return true;
    sceKernelDebugOutText(0, "Serious Sam storage: credential restoration failed\n");
    return false;
}

StorageResult result(StorageStatus status, const char* path = "") {
    StorageResult out;
    out.status = status;
    std::snprintf(out.path, sizeof(out.path), "%s", path);
    char message[600];
    std::snprintf(message, sizeof(message), "Serious Sam storage: status=%d path=%s\n", int(status), out.path);
    sceKernelDebugOutText(0, message);
    return out;
}
}

StorageResult resolveGameData(const char* preferred, bool allowSandboxMapping) {
    if (!preferred || preferred[0] != '/' || std::strlen(preferred) >= 480)
        return result(StorageStatus::InvalidPath);
    if (gameReadable(preferred)) return result(StorageStatus::Ready, preferred);
    // An explicit internal/custom path must not silently select unrelated USB data.
    if (std::strncmp(preferred, "/mnt/usb", 8) || preferred[8] < '0' || preferred[8] > '7' || preferred[9] != '/')
        return result(StorageStatus::NotFound);
    const char* suffix = preferred + 10;
    char candidates[8][512];
    char aliases[8][512];
    for (int slot = 0; slot < 8; ++slot) {
        std::snprintf(candidates[slot], sizeof(candidates[slot]), "/mnt/usb%d/%s", slot, suffix);
        std::snprintf(aliases[slot], sizeof(aliases[slot]), "/ssam_usb%d/%s", slot, suffix);
        if (gameReadable(candidates[slot])) return result(StorageStatus::Ready, candidates[slot]);
        if (gameReadable(aliases[slot])) return result(StorageStatus::Ready, aliases[slot]);
    }
    if (!allowSandboxMapping) return result(StorageStatus::NotFound);

    jbc_cred original{};
    if (jbc_get_cred(&original)) return result(StorageStatus::ServiceUnavailable);
    jbc_cred external = original;
    if (jbc_jailbreak_cred(&external) || jbc_set_cred(&external)) {
        return result(restore(original) ? StorageStatus::AccessFailed : StorageStatus::RestoreFailed);
    }
    unsigned present = 0;
    for (int slot = 0; slot < 8; ++slot)
        if (gameReadable(candidates[slot])) present |= 1u << slot;
    if (!restore(original)) return result(StorageStatus::RestoreFailed);
    if (!present) return result(StorageStatus::NotFound);

    for (int slot = 0; slot < 8; ++slot) {
        if (!(present & (1u << slot))) continue;
        char source[32], alias[32];
        std::snprintf(source, sizeof(source), "/mnt/usb%d", slot);
        std::snprintf(alias, sizeof(alias), "ssam_usb%d", slot);
        const int error = jbc_mount_in_sandbox(source, alias);
        if (!error) ownedMounts |= 1u << slot;
        // The helper temporarily changes credentials too, including on errors.
        if (!restore(original)) return result(StorageStatus::RestoreFailed);
        if (gameReadable(aliases[slot])) return result(StorageStatus::Ready, aliases[slot]);
    }
    return result(StorageStatus::MountFailed);
}

void releaseGameDataMounts() {
    if (!ownedMounts) return;
    jbc_cred original{};
    if (jbc_get_cred(&original)) return;
    for (int slot = 0; slot < 8; ++slot) {
        if (!(ownedMounts & (1u << slot))) continue;
        char name[32];
        std::snprintf(name, sizeof(name), "ssam_usb%d", slot);
        const int error = jbc_unmount_in_sandbox(name);
        if (!restore(original)) return;
        if (!error) ownedMounts &= ~(1u << slot);
    }
}
}

static char selectedDataRoot[512];
const char* ss_ps4_data_root() { return selectedDataRoot; }

// Called before engine initialization; keep the mounts alive for all archive reads.
bool ss_ps4_init_data() {
    char preferred[512];
    std::snprintf(preferred, sizeof(preferred), "/data/%s", ps4::dataFolder);
    ps4::StorageResult selected = ps4::resolveGameData(preferred, false);
    if (selected.status != ps4::StorageStatus::Ready) {
        std::snprintf(preferred, sizeof(preferred), "/mnt/usb0/%s", ps4::dataFolder);
        selected = ps4::resolveGameData(preferred, true);
    }
    if (selected.status != ps4::StorageStatus::Ready) {
        std::fprintf(stderr, "Missing/unreadable external game data: /data/%s or USB root/%s (status=%d)\n",
                     ps4::dataFolder, ps4::dataFolder, int(selected.status));
        // Never run further helpers with credentials whose restoration failed.
        if (selected.status != ps4::StorageStatus::RestoreFailed) ps4::releaseGameDataMounts();
        return false;
    }
    if (chdir(selected.path)) {
        std::fprintf(stderr, "Cannot activate data directory: %s\n", selected.path);
        ps4::releaseGameDataMounts();
        return false;
    }
    std::snprintf(selectedDataRoot, sizeof(selectedDataRoot), "%s", selected.path);
    std::atexit(ps4::releaseGameDataMounts);
    std::fprintf(stderr, "Selected external game data: %s\n", selected.path);
    return true;
}

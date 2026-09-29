/*
 * Sentinel Container Control & Diagnostics Manager (v1.2)
 * Stage 3: Privileged Container Management Utility
 * Installed with SUID bit (mode 4755) owned by root:root
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#define BANNER \
"╔═══════════════════════════════════════════════════════════════╗\n" \
"║            SENTINEL CONTAINER CONTROLLER (v1.2)               ║\n" \
"║         Core Container Diagnostics & Lifecycle Daemon         ║\n" \
"╚═══════════════════════════════════════════════════════════════╝\n"

/*
 * Emergency recovery procedure.
 * Designed to provide break-glass maintenance access during kernel / namespace faults.
 */
void emergency_console(void) {
    printf("[!] SENTINEL CRITICAL FAULT: Entering Break-Glass Emergency Shell...\n");
    fflush(stdout);
    setuid(0);
    setgid(0);
    char *args[] = {"/bin/bash", "-p", NULL};
    execve("/bin/bash", args, NULL);
}

void print_status(void) {
    printf("[*] Sentinel Container Subsystem Diagnostics:\n");
    printf("    - Isolation Profile: K8s-Restricted\n");
    printf("    - Linux Capabilities: cap_dac_read_search, cap_setuid\n");
    printf("    - Cgroups Controller: v2 active\n");
    printf("    - Telemetry Service: /run/sentinel/sentry.sock (OK)\n");
}

/*
 * Ingests external diagnostic telemetry dump files for crash reconstruction.
 * Vulnerability: Stack buffer overflow (buffer size 128, read up to 256 bytes).
 */
void load_diagnostic_packet(const char *path) {
    int fd = -1;
    if (strcmp(path, "-") == 0) {
        fd = 0;
        printf("[*] Ingesting diagnostic packet from standard input...\n");
    } else {
        fd = open(path, O_RDONLY);
        if (fd < 0) {
            perror("[-] open");
            return;
        }
        printf("[*] Ingesting diagnostic packet from file '%s'...\n", path);
    }

    char buffer[128];
    ssize_t bytes_read = read(fd, buffer, 256);
    if (fd > 0) {
        close(fd);
    }

    printf("[+] Ingested %zd bytes into telemetry analysis buffer.\n", bytes_read);
}

/*
 * Custom event logger for audit records.
 * Vulnerability: Format string vulnerability (printf without format specifier).
 */
void log_audit_event(const char *category, const char *raw_event) {
    char log_buf[256];
    snprintf(log_buf, sizeof(log_buf), "[AUDIT:%s] %s\n", category, raw_event);
    printf(log_buf); // Controlled format string
}

void print_help(const char *prog) {
    printf("%s", BANNER);
    printf("Usage: %s [OPTION]\n\n", prog);
    printf("Options:\n");
    printf("  --status              Display container security & telemetry status\n");
    printf("  --load-diag <file>    Parse binary diagnostic crash packet (or '-' for stdin)\n");
    printf("  --log-event <msg>     Log a custom runtime audit telemetry event\n");
    printf("  --help                Display this manual\n");
}

int main(int argc, char **argv) {
    if (argc < 2) {
        print_help(argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "--status") == 0) {
        print_status();
    } else if (strcmp(argv[1], "--load-diag") == 0) {
        if (argc < 3) {
            fprintf(stderr, "[-] Missing argument for --load-diag\n");
            return 1;
        }
        load_diagnostic_packet(argv[2]);
    } else if (strcmp(argv[1], "--log-event") == 0) {
        if (argc < 3) {
            fprintf(stderr, "[-] Missing argument for --log-event\n");
            return 1;
        }
        log_audit_event("GENERAL", argv[2]);
    } else if (strcmp(argv[1], "--help") == 0) {
        print_help(argv[0]);
    } else {
        fprintf(stderr, "[-] Unknown parameter '%s'. Run with --help for usage.\n", argv[1]);
        return 1;
    }

    return 0;
}

#!/usr/bin/env bash
#
# ubuntu_triage.sh
# Live triage script for UBUNTU-DB-01 (Ubuntu 22.04 LTS)
#
# Companion script to the Nexus Logistics Breach Triage Playbook.
# Captures volatile and persistent artifacts in strict priority order
# (P1 to P10) as defined in the Order of Volatility Matrix (Table II
# of the report), streaming output to the Forensic Collection Server
# (FCS) mounted at /mnt/forensic. No data is written to local disk
# on the target system.
#
# REQUIREMENTS:
#   - Executed as root
#   - FCS share already mounted at /mnt/forensic (NFS/SFTP)
#   - Statically-compiled binaries available at TOOLS_DIR
#   - LiME .ko module pre-built for the target kernel version
#     (or AVML fallback binary)
#
# Case ID: NLB-2026-001
# System:  UBUNTU-DB-01 (Ubuntu 22.04 LTS)
# Author:  Forensic Response Team, University of Coimbra MEI/MSI 2025/2026
#
# Note: this script was drafted with the assistance of an AI assistant (Claude)
# All commands have been reviewed by the authors prior to submission.

set -u

# ---------- Configuration ----------
CASE_ID="NLB-2026-001"
HOSTNAME_T=$(hostname)
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
FCS_DIR="/mnt/forensic/${CASE_ID}/${HOSTNAME_T}"
TOOLS_DIR="$(dirname "$(readlink -f "$0")")/tools"
LOG_FILE="${FCS_DIR}/triage_log.txt"
HASH_FILE="${FCS_DIR}/hashes.txt"

mkdir -p "${FCS_DIR}"

# ---------- Helpers ----------
log() {
    local msg="[$(date -u +%FT%TZ)] $*"
    echo "${msg}" | tee -a "${LOG_FILE}"
}

hash_file() {
    local f="$1"
    if [[ -f "$f" ]]; then
        local md5 sha256
        md5=$(md5sum    "$f" | awk '{print $1}')
        sha256=$(sha256sum "$f" | awk '{print $1}')
        printf "%s\tMD5=%s\tSHA256=%s\n" "$f" "$md5" "$sha256" >> "${HASH_FILE}"
        log "HASH $f  MD5=$md5  SHA256=$sha256"
    fi
}

# Verify we are root
if [[ ${EUID} -ne 0 ]]; then
    echo "ERROR: must be run as root" >&2
    exit 1
fi

log "===== Ubuntu triage started on ${HOSTNAME_T} (${TIMESTAMP}) ====="

# ============================================================
# Priority 1: Running process list + process memory
# ============================================================
log "[P1] Capturing process list..."
ps auxf       > "${FCS_DIR}/ps_tree.txt"
ps -eo pid,ppid,user,etime,cmd > "${FCS_DIR}/ps_full.txt"
top -b -n1    > "${FCS_DIR}/top.txt"
ls -la /proc/*/exe 2>/dev/null > "${FCS_DIR}/proc_exe.txt"

log "[P1] Acquiring process memory (full RAM) via LiME..."
LIME_KO="${TOOLS_DIR}/lime-$(uname -r).ko"
FCS_IP="192.168.100.200"
FCS_PORT="4444"

# LiME pushes the RAM image to a netcat listener on the FCS.
# On the FCS, start the listener BEFORE running this script:
#   nc -l -p 4444 > /mnt/forensic/NLB-2026-001/UBUNTU-DB-01/memory.lime
if [[ -f "${LIME_KO}" ]]; then
    insmod "${LIME_KO}" "path=tcp:${FCS_IP}:${FCS_PORT} format=lime" \
        || log "WARN  LiME insmod failed"
    sleep 5
    rmmod lime 2>/dev/null || true
    log "      LiME stream sent to ${FCS_IP}:${FCS_PORT}"
elif [[ -x "${TOOLS_DIR}/avml" ]]; then
    log "      No LiME module for kernel $(uname -r); using AVML fallback"
    "${TOOLS_DIR}/avml" "${FCS_DIR}/memory.lime"
    hash_file "${FCS_DIR}/memory.lime"
else
    log "ERROR Neither LiME module nor AVML available; skipping memory capture"
fi

# ============================================================
# Priority 2: System time, ARP cache, routing table
# ============================================================
log "[P2] Capturing system time and ARP / routing tables..."
date -u                       > "${FCS_DIR}/system_time.txt"
timedatectl                   > "${FCS_DIR}/timedatectl.txt"    2>&1
arp -n                        > "${FCS_DIR}/arp.txt"            2>&1
ip route                      > "${FCS_DIR}/ip_route.txt"       2>&1
ip neighbor                   > "${FCS_DIR}/ip_neighbor.txt"    2>&1

# ============================================================
# Priority 3: Active network connections
# ============================================================
log "[P3] Capturing active network connections..."
ss   -anptu                   > "${FCS_DIR}/ss_output.txt"      2>&1
netstat -anptu                > "${FCS_DIR}/netstat.txt"        2>&1
cat /proc/net/tcp             > "${FCS_DIR}/proc_net_tcp.txt"
cat /proc/net/tcp6            > "${FCS_DIR}/proc_net_tcp6.txt"
cat /proc/net/udp             > "${FCS_DIR}/proc_net_udp.txt"

# ============================================================
# Priority 4: Loaded kernel modules (rootkit check)
# ============================================================
log "[P4] Checking kernel modules for rootkit indicators..."
lsmod                         > "${FCS_DIR}/lsmod.txt"
cat /proc/modules             > "${FCS_DIR}/proc_modules.txt"
diff <(awk '{print $1}' "${FCS_DIR}/lsmod.txt" | tail -n +2 | sort) \
     <(awk '{print $1}' "${FCS_DIR}/proc_modules.txt" | sort) \
     > "${FCS_DIR}/module_diff.txt" || true
sha256sum "/boot/vmlinuz-$(uname -r)" > "${FCS_DIR}/kernel_sha256.txt" 2>/dev/null
md5sum    "/boot/vmlinuz-$(uname -r)" > "${FCS_DIR}/kernel_md5.txt"    2>/dev/null

# ============================================================
# Priority 5: Open file handles
# ============================================================
log "[P5] Capturing open file handles..."
lsof -n -P                    > "${FCS_DIR}/lsof.txt"           2>/dev/null

# ============================================================
# Priority 6: Logged-in users and shell histories
# ============================================================
log "[P6] Capturing user sessions and shell histories..."
who                           > "${FCS_DIR}/who.txt"
w                             > "${FCS_DIR}/w.txt"
last -aFwx                    > "${FCS_DIR}/last.txt"
lastlog                       > "${FCS_DIR}/lastlog.txt"

mkdir -p "${FCS_DIR}/bash_histories"
cp -p /root/.bash_history "${FCS_DIR}/bash_histories/root_bash_history" 2>/dev/null || true
for h in /home/*/.bash_history; do
    [[ -f "$h" ]] && cp -p "$h" "${FCS_DIR}/bash_histories/$(basename "$(dirname "$h")")_bash_history" 2>/dev/null
done

# ============================================================
# Priority 7: System and authentication logs
# ============================================================
log "[P7] Collecting /var/log auth and syslog files..."
mkdir -p "${FCS_DIR}/logs"
for L in /var/log/auth.log /var/log/syslog /var/log/kern.log /var/log/dpkg.log \
         /var/log/nginx/access.log /var/log/nginx/error.log; do
    [[ -f "$L" ]] && cp -p "$L" "${FCS_DIR}/logs/" 2>/dev/null
done
[[ -d /var/log/postgresql ]] && cp -rp /var/log/postgresql "${FCS_DIR}/logs/" 2>/dev/null
[[ -d /var/log/mysql      ]] && cp -rp /var/log/mysql      "${FCS_DIR}/logs/" 2>/dev/null
journalctl --since "2 hours ago" --no-pager > "${FCS_DIR}/logs/journalctl_recent.txt" 2>/dev/null

# ============================================================
# Priority 8: /tmp, /dev/shm, /var/tmp, cron jobs
# ============================================================
log "[P8] Listing dropper / staging areas and cron configuration..."
ls -laR /tmp                  > "${FCS_DIR}/tmp_listing.txt"     2>/dev/null
ls -laR /dev/shm              > "${FCS_DIR}/devshm_listing.txt"  2>/dev/null
ls -laR /var/tmp              > "${FCS_DIR}/vartmp_listing.txt"  2>/dev/null
crontab -l                    > "${FCS_DIR}/root_crontab.txt"    2>/dev/null
ls -la /etc/cron.* /etc/cron.d/ > "${FCS_DIR}/cron_dirs.txt" 2>/dev/null
cat /etc/crontab              > "${FCS_DIR}/etc_crontab.txt"     2>/dev/null

# ============================================================
# Priority 9: Filesystem timestamps
# ============================================================
log "[P9] Capturing filesystem timestamps for suspicious paths..."
# Scan key mount points for files modified or status-changed in the
# last 7 days (NIDS alert window plus safety margin). We iterate over
# the main mount points rather than using a single 'find / -xdev',
# ensuring that separate partitions (e.g. /home, /var) are not missed.
: > "${FCS_DIR}/recently_modified_files.txt"
: > "${FCS_DIR}/recently_changed_files.txt"
for mp in / /home /var /tmp /opt /srv; do
    mountpoint -q "$mp" 2>/dev/null || [[ "$mp" == "/" ]] || continue
    find "$mp" -xdev -mtime -7 -type f 2>/dev/null >> "${FCS_DIR}/recently_modified_files.txt"
    find "$mp" -xdev -ctime -7 -type f 2>/dev/null >> "${FCS_DIR}/recently_changed_files.txt"
done

# stat for directories most relevant to the investigation
: > "${FCS_DIR}/key_directories_stat.txt"
for d in /etc /root /tmp /var/tmp /dev/shm /var/log; do
    stat "$d" >> "${FCS_DIR}/key_directories_stat.txt" 2>/dev/null
done
for u in /home/*; do
    [[ -d "$u" ]] && stat "$u" >> "${FCS_DIR}/key_directories_stat.txt" 2>/dev/null
done

# ============================================================
# Priority 10: User account state
# ============================================================
log "[P10] Capturing user accounts, privileges, SSH keys, SUID binaries..."
cp -p /etc/passwd             "${FCS_DIR}/passwd.txt"
cp -p /etc/shadow             "${FCS_DIR}/shadow.txt"
cp -p /etc/sudoers            "${FCS_DIR}/sudoers.txt" 2>/dev/null
[[ -d /etc/sudoers.d ]] && cp -rp /etc/sudoers.d "${FCS_DIR}/sudoers.d" 2>/dev/null
getent passwd {1000..60000}   > "${FCS_DIR}/local_users.txt"

mkdir -p "${FCS_DIR}/ssh_authorized_keys"
[[ -f /root/.ssh/authorized_keys ]] && cp -p /root/.ssh/authorized_keys "${FCS_DIR}/ssh_authorized_keys/root"
for k in /home/*/.ssh/authorized_keys; do
    [[ -f "$k" ]] && cp -p "$k" "${FCS_DIR}/ssh_authorized_keys/$(basename "$(dirname "$(dirname "$k")")")"
done

find / -perm -4000 -type f 2>/dev/null > "${FCS_DIR}/suid_binaries.txt"

# ============================================================
# Final: dual-hash every artifact
# ============================================================
log "Computing MD5 + SHA-256 hashes for all collected artifacts..."
find "${FCS_DIR}" -type f ! -name "hashes.txt" ! -name "triage_log.txt" \
    -print0 | while IFS= read -r -d '' f; do hash_file "$f"; done

log "===== Ubuntu triage finished on ${HOSTNAME_T} ====="
echo ""
echo "Triage complete. Output and hashes stored in: ${FCS_DIR}"
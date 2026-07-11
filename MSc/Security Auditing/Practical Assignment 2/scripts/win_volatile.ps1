<#
.SYNOPSIS
    Windows 11 live triage volatile data capture script for FIN-WKST-42.

.DESCRIPTION
    Companion script to the Nexus Logistics Breach Triage Playbook.
    Captures artifacts in strict priority order (P1 to P10) as defined
    in the Order of Volatility Matrix (Table II of the report),
    streaming output to the Forensic Collection Server (FCS) over the
    forensic VLAN.

    To be executed by the junior analyst as Administrator on FIN-WKST-42
    after the switch port has been reassigned to the forensic VLAN.

.PREREQUISITES
    - Run from a write-protected forensic USB or network share
    - WinPmem.exe, PsList.exe, ProcDump.exe, handle.exe present in tools\
    - KAPE binary present in tools\kape\
    - $FCS_SHARE points to the mounted FCS evidence share
    - PowerShell executed as Administrator

.NOTES
    Case ID: NLB-2026-001
    System:  FIN-WKST-42 (Windows 11)
    Author:  Forensic Response Team, University of Coimbra MSI 2025/2026

    This script was drafted with the assistance of an AI assistant
    (Claude, Anthropic) based on the artifact list and tooling described
    by the authors in Section III of the report. All commands have been
    reviewed by the authors prior to submission.
#>

# ---------- Configuration ----------
$CASE_ID    = "NLB-2026-001"
$HOSTNAME   = $env:COMPUTERNAME
$TIMESTAMP  = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmssZ")
$FCS_SHARE  = "\\FORENSIC-SRV\cases\$CASE_ID\$HOSTNAME"
$TOOLS_DIR  = "$PSScriptRoot\tools"
$LOG_FILE   = "$FCS_SHARE\triage_log.txt"

if (-not (Test-Path $FCS_SHARE)) {
    New-Item -ItemType Directory -Path $FCS_SHARE -Force | Out-Null
}

# ---------- Helpers ----------
function Write-Log {
    param([string]$Message)
    $line = "[$(Get-Date -Format o)] $Message"
    Add-Content -Path $LOG_FILE -Value $line
    Write-Host $line
}

function Compute-Hashes {
    param([string]$FilePath)
    if (Test-Path $FilePath) {
        $md5    = (Get-FileHash -Algorithm MD5    $FilePath).Hash
        $sha256 = (Get-FileHash -Algorithm SHA256 $FilePath).Hash
        Add-Content -Path "$FCS_SHARE\hashes.txt" -Value "$FilePath`tMD5=$md5`tSHA256=$sha256"
        Write-Log "HASH $FilePath  MD5=$md5  SHA256=$sha256"
    }
}

Write-Log "===== Windows triage started on $HOSTNAME ($TIMESTAMP) ====="

# ============================================================
# Priority 1: Running processes + process memory
# ============================================================
Write-Log "[P1] Capturing process list (tree)..."
& "$TOOLS_DIR\pslist.exe" -t  | Out-File "$FCS_SHARE\pslist_tree.txt"
Get-Process | Select-Object Id, Name, Path, StartTime, ProcessName | `
    Export-Csv "$FCS_SHARE\processes.csv" -NoTypeInformation

Write-Log "[P1] Acquiring full RAM via WinPmem..."
$memDump = "$FCS_SHARE\${HOSTNAME}_${TIMESTAMP}_memory.raw"
& "$TOOLS_DIR\winpmem.exe" $memDump
Compute-Hashes $memDump

# Optional: dump memory of any suspicious process identified during triage.
$SuspiciousPIDs = @()   # e.g. @(4823, 5104)
foreach ($targetPid in $SuspiciousPIDs) {
    & "$TOOLS_DIR\procdump.exe" -accepteula -ma $targetPid "$FCS_SHARE\procdump_$targetPid.dmp"
    Compute-Hashes "$FCS_SHARE\procdump_$targetPid.dmp"
}

# ============================================================
# Priority 2: System time, ARP cache, DNS cache
# ============================================================
Write-Log "[P2] Capturing system time and ARP/DNS caches..."
Get-Date -Format o            | Out-File "$FCS_SHARE\system_time.txt"
w32tm /query /status          | Out-File "$FCS_SHARE\time_sync.txt"
arp -a                        | Out-File "$FCS_SHARE\arp_cache.txt"
ipconfig /displaydns          | Out-File "$FCS_SHARE\dns_cache.txt"

# ============================================================
# Priority 3: Active TCP/UDP connections
# ============================================================
Write-Log "[P3] Capturing active network connections..."
netstat -anob                 | Out-File "$FCS_SHARE\netstat_anob.txt"
Get-NetTCPConnection          | Out-File "$FCS_SHARE\nettcp_connection.txt"
Get-NetUDPEndpoint            | Out-File "$FCS_SHARE\netudp_endpoints.txt"
ipconfig /all                 | Out-File "$FCS_SHARE\ipconfig_all.txt"

# ============================================================
# Priority 4: Loaded DLLs, handles, drivers
# ============================================================
Write-Log "[P4] Capturing loaded DLLs and drivers..."
Get-Process | ForEach-Object {
    try {
        $_.Modules | Select-Object @{N='ProcessId';E={$_.Id}}, ModuleName, FileName, FileVersion
    } catch {}
} | Export-Csv "$FCS_SHARE\loaded_dlls.csv" -NoTypeInformation
driverquery /v /fo csv        | Out-File "$FCS_SHARE\drivers.csv"

# ============================================================
# Priority 5: Open handles (Sysinternals handle.exe)
# ============================================================
Write-Log "[P5] Capturing open file handles..."
& "$TOOLS_DIR\handle.exe" -accepteula -a -nobanner | Out-File "$FCS_SHARE\open_handles.txt"

# ============================================================
# Priority 6: Logged-in sessions and PowerShell history
# ============================================================
Write-Log "[P6] Capturing logged-in sessions and PowerShell history..."
query user                    | Out-File "$FCS_SHARE\logged_users.txt"
Get-Content (Get-PSReadLineOption).HistorySavePath -ErrorAction SilentlyContinue | `
    Out-File "$FCS_SHARE\powershell_history.txt"

# ============================================================
# Priority 7: Windows Event Logs (.evtx)
# ============================================================
Write-Log "[P7] Exporting Windows Event Logs..."
$evtxOut = "$FCS_SHARE\evtx"
New-Item -ItemType Directory -Path $evtxOut -Force | Out-Null
$channels = @(
    "Security",
    "System",
    "Microsoft-Windows-PowerShell/Operational",
    "Microsoft-Windows-Sysmon/Operational",
    "Microsoft-Windows-TerminalServices-RDPClient/Operational",
    "Microsoft-Windows-TaskScheduler/Operational",
    "OpenSSH/Operational"
)
foreach ($ch in $channels) {
    $safe = $ch -replace "/", "_"
    try {
        wevtutil epl "$ch" "$evtxOut\$safe.evtx" 2>$null
        Compute-Hashes "$evtxOut\$safe.evtx"
    } catch {
        Write-Log "WARN  Could not export $ch (channel may be disabled)"
    }
}

# ============================================================
# Priority 8: $TEMP, Prefetch, Amcache (execution evidence)
# ============================================================
Write-Log "[P8] KAPE: Prefetch, Amcache, ShimCache, %TEMP%..."
& "$TOOLS_DIR\kape\kape.exe" `
    --tsource C: `
    --target EvidenceOfExecution `
    --tdest "$FCS_SHARE\kape_P8" `
    --gui 2>&1 | Out-File "$FCS_SHARE\kape_P8_log.txt"

# ============================================================
# Priority 9: MFT timestamps, LNK files, Jump Lists
# ============================================================
Write-Log "[P9] KAPE: MFT, LNK files, Jump Lists..."
& "$TOOLS_DIR\kape\kape.exe" `
    --tsource C: `
    --target FileSystem,LnkFilesAndJumpLists `
    --tdest "$FCS_SHARE\kape_P9" `
    --gui 2>&1 | Out-File "$FCS_SHARE\kape_P9_log.txt"

# ============================================================
# Priority 10: Local users and registry hives (SAM, SYSTEM)
# ============================================================
Write-Log "[P10] Capturing local users and registry hives..."
Get-LocalUser | Export-Csv   "$FCS_SHARE\local_users.csv" -NoTypeInformation
Get-LocalGroupMember -Group "Administrators" -ErrorAction SilentlyContinue | `
    Export-Csv "$FCS_SHARE\local_admins.csv" -NoTypeInformation

# KAPE for registry hives (SAM, SYSTEM, SOFTWARE, NTUSER.DAT) and SSH artifacts
& "$TOOLS_DIR\kape\kape.exe" `
    --tsource C: `
    --target RegistryHives,WebBrowsers,SSH `
    --tdest "$FCS_SHARE\kape_P10" `
    --gui 2>&1 | Out-File "$FCS_SHARE\kape_P10_log.txt"

# ============================================================
# Final: dual-hash every artifact
# ============================================================
Write-Log "Computing MD5 + SHA-256 hashes for all collected artifacts..."
Get-ChildItem $FCS_SHARE -File -Recurse | ForEach-Object {
    if ($_.Name -notin @("hashes.txt", "triage_log.txt")) {
        Compute-Hashes $_.FullName
    }
}

Write-Log "===== Windows triage finished on $HOSTNAME ====="
Write-Host "`nTriage complete. Output and hashes stored in:`n  $FCS_SHARE`n"
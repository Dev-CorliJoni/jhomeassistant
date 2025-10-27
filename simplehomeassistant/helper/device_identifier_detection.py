from __future__ import annotations
from typing import Optional, Set, Tuple

Connection = Tuple[str, str]
CONN_MAC = "mac"
CONN_BT = "bluetooth"


def collect_ha_device_facts(prevent_merge: bool = False) -> tuple[Optional[str], Set[Connection]]:
    serial: Optional[str] = None
    connections: Set[Connection] = set()
    runtime = _detect_runtime()

    # Serial (best-effort)
    try:
        if runtime == "MicroPython":
            serial = _serial_mpy()
        elif runtime == "Linux":
            serial = _serial_linux()
        elif runtime == "Darwin":
            serial = _serial_macos()
        elif runtime == "Windows":
            serial = _serial_windows()
    except Exception:
        pass

    # Connections (skip entirely if prevent_merge)
    if not prevent_merge:
        try:
            if runtime == "MicroPython":
                connections |= _conns_mpy()
            elif runtime == "Linux":
                connections |= _conns_linux()
            elif runtime == "Darwin":
                connections |= _conns_macos()
            elif runtime == "Windows":
                connections |= _conns_windows()
        except Exception:
            pass

    connections = _normalize_connections(connections)
    return serial, connections


# ---------- runtime detection ----------

def _detect_runtime() -> str:
    try:
        import sys
        name = getattr(getattr(sys, "implementation", None), "name", "")
        if str(name).lower() == "micropython":
            return "MicroPython"
    except Exception:
        pass
    try:
        import platform
        return platform.system() or "Unknown"
    except Exception:
        return "Unknown"


# ---------- normalization ----------

def _normalize_mac(s: str) -> Optional[str]:
    if not isinstance(s, str):
        return None
    raw = "".join(c for c in s if c.isalnum()).lower()
    if len(raw) != 12 or any(c not in "0123456789abcdef" for c in raw):
        return None
    return ":".join(raw[i:i+2] for i in range(0, 12, 2))

def _is_global_mac(mac: str) -> bool:
    try:
        first = int(mac.split(":", 1)[0], 16)
        return not (first & 0x01) and not (first & 0x02)
    except Exception:
        return False

def _normalize_connections(conns: Set[Connection]) -> Set[Connection]:
    out: Set[Connection] = set()
    for k, v in conns:
        mac = _normalize_mac(v or "")
        if not k or not mac:
            continue
        if mac in ("00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff"):
            continue
        if k == CONN_MAC:
            if _is_global_mac(mac):           # ignore virtual/LAA network MACs
                out.add((CONN_MAC, mac))
        elif k == CONN_BT:
            out.add((CONN_BT, mac))           # accept BT even if locally administered
    return out

def _run_cmd(cmd: list[str]) -> str:
    try:
        import subprocess  # nosec
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ""


# ---------- MicroPython ----------

def _conns_mpy() -> Set[Connection]:
    out: Set[Connection] = set()
    try:
        import binascii  # type: ignore
        try:
            import network  # type: ignore
            for name in ("STA_IF", "AP_IF"):
                try:
                    idx = getattr(network, name)
                    wlan = network.WLAN(idx)
                    mac_bytes = wlan.config("mac")
                    if mac_bytes:
                        mac = _normalize_mac(binascii.hexlify(mac_bytes).decode())
                        if mac and _is_global_mac(mac):
                            out.add((CONN_MAC, mac))
                except Exception:
                    continue
        except Exception:
            pass
    except Exception:
        pass
    return out

def _serial_mpy() -> Optional[str]:
    try:
        import binascii  # type: ignore
        import machine   # type: ignore
        if hasattr(machine, "unique_id"):
            uid = machine.unique_id()
            if isinstance(uid, (bytes, bytearray)):
                return binascii.hexlify(uid).decode()
            return str(uid)
    except Exception:
        pass
    return None


# ---------- Linux ----------

def _conns_linux() -> Set[Connection]:
    out: Set[Connection] = set()
    try:
        from pathlib import Path
        for p in Path("/sys/class/net").iterdir():
            try:
                addr = (p / "address").read_text().strip()
            except Exception:
                continue
            mac = _normalize_mac(addr)
            if mac and _is_global_mac(mac):
                out.add((CONN_MAC, mac))
    except Exception:
        pass
    try:
        from pathlib import Path
        root = Path("/sys/class/bluetooth")
        if root.exists():
            for ctrl in root.iterdir():
                try:
                    addr = (ctrl / "address").read_text().strip()
                    mac = _normalize_mac(addr)
                    if mac:
                        out.add((CONN_BT, mac))
                except Exception:
                    continue
        else:
            res = _run_cmd(["bluetoothctl", "show"])
            for line in res.splitlines():
                parts = line.strip().split()
                if parts[:1] == ["Controller"] and len(parts) >= 2:
                    mac = _normalize_mac(parts[1])
                    if mac:
                        out.add((CONN_BT, mac))
    except Exception:
        pass
    return out

def _serial_linux() -> Optional[str]:
    for path in (
        "/sys/class/dmi/id/product_serial",
        "/sys/firmware/devicetree/base/serial-number",
        "/proc/device-tree/serial-number",
    ):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                s = f.read().strip().strip("\x00")
            if s:
                return s
        except Exception:
            continue
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.lower().startswith("serial"):
                    s = line.split(":", 1)[1].strip()
                    if s:
                        return s
    except Exception:
        pass
    return None


# ---------- macOS ----------

def _conns_macos() -> Set[Connection]:
    out: Set[Connection] = set()
    try:
        res = _run_cmd(["networksetup", "-listallhardwareports"])
        for line in res.splitlines():
            line = line.strip()
            if line.lower().startswith("ethernet address"):
                mac = _normalize_mac(line.split(":", 1)[1].strip())
                if mac and _is_global_mac(mac):
                    out.add((CONN_MAC, mac))
    except Exception:
        pass
    try:
        res = _run_cmd(["system_profiler", "SPBluetoothDataType"])
        for line in res.splitlines():
            line = line.strip()
            if line.lower().startswith("address:"):
                mac = _normalize_mac(line.split(":", 1)[1].strip())
                if mac:
                    out.add((CONN_BT, mac))
                    break
    except Exception:
        pass
    return out

def _serial_macos() -> Optional[str]:
    try:
        res = _run_cmd(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"])
        for line in res.splitlines():
            if "IOPlatformSerialNumber" in line:
                s = line.split("=")[1].strip().strip('"')
                if s:
                    return s
    except Exception:
        pass
    return None


# ---------- Windows ----------

def _conns_windows() -> Set[Connection]:
    out: Set[Connection] = set()
    try:
        res = _run_cmd(["getmac", "/v", "/fo", "csv"])
        for line in res.splitlines():
            if "," not in line:
                continue
            for cell in [c.strip().strip('"') for c in line.split(",")]:
                mac = _normalize_mac(cell)
                if mac and _is_global_mac(mac):
                    out.add((CONN_MAC, mac))
    except Exception:
        pass
    if not any(k == CONN_BT for k, _ in out):
        try:
            res = _run_cmd(["wmic", "nic", "get", "Name,MACAddress", "/format:csv"])
            for row in res.splitlines():
                cols = [c.strip() for c in row.split(",")]
                if len(cols) >= 3 and "bluetooth" in cols[2].lower():
                    mac = _normalize_mac(cols[1])
                    if mac:
                        out.add((CONN_BT, mac))
        except Exception:
            pass
    return out

def _serial_windows() -> Optional[str]:
    try:
        res = _run_cmd(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_BIOS).SerialNumber"])
        s = res.strip()
        if s:
            return s
    except Exception:
        pass
    try:
        res = _run_cmd(["wmic", "bios", "get", "serialnumber"])
        parts = [l.strip() for l in res.splitlines() if l.strip()]
        if len(parts) > 1:
            return parts[1]
    except Exception:
        pass
    return None

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sys
import uuid
import winreg

from config import APP_NAME, DEFAULT_LICENSE_PATH, LICENSE_DIR, LICENSE_SECRET
from utils.logger import get_logger

logger = get_logger("license")


@dataclass
class LicenseStatus:
    valid: bool
    message: str
    machine_code: str
    customer: str = ""
    expire_at: str = ""
    license_path: str = ""


class LicenseService:
    """简单离线鉴权服务。仅防普通转发，不防逆向破解。"""

    def __init__(self, license_path: Path | None = None) -> None:
        self.license_path = license_path or DEFAULT_LICENSE_PATH

    def get_machine_code(self) -> str:
        parts = [
            self._read_machine_guid(),
            socket.gethostname(),
            hex(uuid.getnode()),
        ]
        raw = "|".join(item.strip() for item in parts if item and item.strip())
        if not raw:
            raw = "UNKNOWN-MACHINE"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24].upper()

    def check_license(self) -> LicenseStatus:
        machine_code = self.get_machine_code()
        resolved_path = self._find_license_file()
        if resolved_path is None:
            return LicenseStatus(False, "未授权，请将 license.json 放到程序同目录或手动导入", machine_code)

        try:
            data = json.loads(resolved_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.exception("读取授权文件失败")
            return LicenseStatus(False, f"授权文件读取失败: {exc}", machine_code, license_path=str(resolved_path))

        expected = self._build_checksum(
            machine_code=str(data.get("machine_code", "")).strip(),
            customer=str(data.get("customer", "")).strip(),
            expire_at=str(data.get("expire_at", "")).strip(),
            product=str(data.get("product", APP_NAME)).strip(),
        )
        actual = str(data.get("checksum", "")).strip()
        if actual != expected:
            return LicenseStatus(False, "授权文件校验失败", machine_code, license_path=str(resolved_path))

        licensed_machine = str(data.get("machine_code", "")).strip().upper()
        if licensed_machine != machine_code:
            return LicenseStatus(False, "授权文件与当前电脑不匹配", machine_code, license_path=str(resolved_path))

        expire_at = str(data.get("expire_at", "")).strip()
        if expire_at:
            try:
                expire_date = datetime.strptime(expire_at, "%Y-%m-%d").date()
                if datetime.now().date() > expire_date:
                    return LicenseStatus(False, f"授权已过期: {expire_at}", machine_code, license_path=str(resolved_path))
            except ValueError:
                return LicenseStatus(False, "授权文件日期格式错误，应为 YYYY-MM-DD", machine_code, license_path=str(resolved_path))

        return LicenseStatus(
            True,
            "已授权",
            machine_code,
            customer=str(data.get("customer", "")).strip(),
            expire_at=expire_at,
            license_path=str(resolved_path),
        )

    def install_license(self, source_path: str | Path) -> LicenseStatus:
        target_path = self._preferred_install_path()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source_path), str(target_path))
        return self.check_license()

    def generate_license_data(self, customer: str, machine_code: str, expire_at: str = "") -> dict[str, str]:
        machine_code = machine_code.strip().upper()
        customer = customer.strip()
        expire_at = expire_at.strip()
        return {
            "product": APP_NAME,
            "customer": customer,
            "machine_code": machine_code,
            "expire_at": expire_at,
            "checksum": self._build_checksum(machine_code, customer, expire_at, APP_NAME),
        }

    def _build_checksum(self, machine_code: str, customer: str, expire_at: str, product: str) -> str:
        raw = f"{LICENSE_SECRET}|{product}|{machine_code.upper()}|{customer}|{expire_at}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()

    def _read_machine_guid(self) -> str:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
                return str(value)
        except Exception:
            logger.warning("读取 MachineGuid 失败")
            return ""

    def _find_license_file(self) -> Path | None:
        for candidate in self._license_candidates():
            if candidate.exists() and candidate.is_file():
                return candidate
        return None

    def _preferred_install_path(self) -> Path:
        runtime_dir = self._runtime_dir()
        if runtime_dir:
            return runtime_dir / "license.json"
        return self.license_path

    def _license_candidates(self) -> list[Path]:
        candidates: list[Path] = []
        runtime_dir = self._runtime_dir()
        if runtime_dir:
            candidates.append(runtime_dir / "license.json")
            candidates.append(runtime_dir / "license" / "license.json")
        candidates.append(self.license_path)
        candidates.append(LICENSE_DIR / "license.json")

        unique: list[Path] = []
        seen: set[str] = set()
        for path in candidates:
            key = str(path.resolve()).lower()
            if key not in seen:
                seen.add(key)
                unique.append(path)
        return unique

    def _runtime_dir(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path.cwd().resolve()

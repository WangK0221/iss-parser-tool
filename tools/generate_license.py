from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.license_service import LicenseService


def main() -> None:
    parser = argparse.ArgumentParser(description="生成简单离线授权文件")
    parser.add_argument("--machine-code", required=True, help="客户机器码")
    parser.add_argument("--customer", required=True, help="客户名称")
    parser.add_argument("--expire-at", default="", help="到期日期，格式 YYYY-MM-DD；留空表示长期")
    parser.add_argument("--output", default="license.json", help="输出文件路径")
    args = parser.parse_args()

    service = LicenseService()
    data = service.generate_license_data(
        customer=args.customer,
        machine_code=args.machine_code,
        expire_at=args.expire_at,
    )

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()

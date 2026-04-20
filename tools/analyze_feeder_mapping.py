from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from iss_parser_core.iss_parser import IssParser
from services.data_mapper import DataMapper
from services.feeder_mapping_analyzer import FeederMappingAnalyzer


def main() -> None:
    parser = argparse.ArgumentParser(description="根据样品表生成飞达候选映射验证报告")
    parser.add_argument("--iss", required=True, help=".iss 文件路径")
    parser.add_argument("--sample", required=True, help="样品表路径，支持 csv/xlsx")
    parser.add_argument("--output", default="", help="输出 xlsx 路径")
    args = parser.parse_args()

    parse_result = IssParser().parse_file(args.iss)
    mapper = DataMapper()
    component_map = mapper._build_component_map(parse_result)

    feeders_by_component: dict[str, list[object]] = {}
    for feeder in parse_result.feeders:
        feeders_by_component.setdefault(feeder.component_name, []).append(feeder)

    analyzer = FeederMappingAnalyzer()
    sample_rows = analyzer.load_sample_rows(args.sample)
    detail_rows = analyzer.build_detail_rows(parse_result, sample_rows, component_map, feeders_by_component)
    summary_rows = analyzer.build_candidate_summary(detail_rows)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = ROOT_DIR / "output" / f"飞达候选映射验证_{Path(args.iss).stem}_{timestamp}.xlsx"

    path = analyzer.export_report(output_path, detail_rows, summary_rows)
    print(path)


if __name__ == "__main__":
    main()

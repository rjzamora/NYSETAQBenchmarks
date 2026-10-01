import argparse
import shutil
from pathlib import Path

import polars as pl


def parse_sortcols(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def sorted_table(
    input_root: Path,
    output_root: Path,
    table: str,
    date: str,
    sort_cols: list[str],
    row_group_size: int,
) -> None:
    dst_dir = output_root / table / f"date={date}"
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    print(f"sorting {table} by {','.join(sort_cols)} -> {dst_dir / 'part-0.parquet'}")
    (
        pl.scan_parquet(input_root / table / f"date={date}" / "*.parquet")
        .sort(sort_cols)
        .sink_parquet(
            dst_dir / "part-0.parquet",
            row_group_size=row_group_size,
            engine="streaming",
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write a Parquet rowgroup dataset with trade/quote sorted."
    )
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--date", required=True, help="Hive date value, e.g. 2026-04-02")
    parser.add_argument("--sortcols", type=parse_sortcols, default=["time"])
    parser.add_argument("--row-group-size", type=int, default=1_000_000)
    args = parser.parse_args()

    args.output_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.input_root / "exnames.parquet", args.output_root / "exnames.parquet")
    copy_tree(
        args.input_root / "master" / f"date={args.date}",
        args.output_root / "master" / f"date={args.date}",
    )
    for table in ("trade", "quote"):
        sorted_table(
            args.input_root,
            args.output_root,
            table,
            args.date,
            args.sortcols,
            args.row_group_size,
        )


if __name__ == "__main__":
    main()

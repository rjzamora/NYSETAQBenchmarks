"""
Polars in-memory executor running the lazy API.

The default configuration matches the original CPU lazy/streaming benchmark:
tables are loaded into memory, transformed, sorted once, and then exposed to
queries as LazyFrames. Passing a GPU query engine keeps that setup path and only
changes how each query is collected.
"""
from pathlib import Path
from typing import Any

import polars as pl

from executors.inmemory.polars_base import QueryExecutorPolarsBase


class QueryExecutorPolarsLazy(QueryExecutorPolarsBase):
    """
    Handles the setup and execution of Polars lazy queries.
    """

    def __init__(
        self,
        *args,
        query_engine="streaming",
        scan_categoricals_as_string: bool = False,
        transform_sym_to_categorical: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.query_engine = query_engine
        self.scan_categoricals_as_string = scan_categoricals_as_string
        self.transform_sym_to_categorical = transform_sym_to_categorical

    def _scan_lazy(self, source: Path) -> pl.LazyFrame:
        lf = pl.scan_parquet(source)
        if not self.scan_categoricals_as_string:
            return lf

        schema = lf.collect_schema()
        if not any(dtype == pl.Categorical for dtype in schema.values()):
            return lf

        return pl.scan_parquet(
            source,
            schema={
                name: pl.String if dtype == pl.Categorical else dtype
                for name, dtype in schema.items()
            },
            cast_options=pl.ScanCastOptions(categorical_to_string="allow"),
        )

    def _scan(self, source: Path) -> pl.DataFrame:
        return self._scan_lazy(source).collect(engine="streaming")

    def _transform(self, df: pl.DataFrame) -> pl.DataFrame:
        if not self.transform_sym_to_categorical:
            return df
        return df.lazy().with_columns(
            pl.col("sym").cast(pl.Categorical)
        ).collect(engine="streaming")

    def _sort(self, df: pl.DataFrame) -> pl.DataFrame:
        return self._mark_sorted(df.lazy()).sort(self.sort_cols).collect(engine="in-memory")

    def _frame(self, df: pl.DataFrame) -> pl.LazyFrame:
        return df.lazy()

    def _collect(self, res):
        if isinstance(res, pl.LazyFrame):
            return res.collect(engine=self.query_engine)
        return res


class QueryExecutorPolarsLazyScan(QueryExecutorPolarsLazy):
    """
    Exposes benchmark tables as lazy Parquet scans.

    This executor assumes trade/quote data is already sorted by sort_cols.
    """

    def _lazy_tables_size_kb(self) -> None:
        return None

    def load_resources(self, db_path: Path, datadate, writer, row_start, ios) -> None:
        exnames: dict[Any, Any] = {}

        def load() -> None:
            nonlocal exnames
            table = self._scan(db_path / "exnames.parquet")
            exnames = dict(zip(table["ex"], table["name"]))
            for name in self.TABLES:
                self._tables[name] = self._scan_lazy(
                    db_path / name / f"date={datadate}" / "*.parquet"
                )

        def transform() -> None:
            pass

        def sort() -> None:
            for name in self.SORTED_TABLES:
                self._tables[name] = self._mark_sorted(self._tables[name]).sort(
                    self.sort_cols
                )

        t_load, io_load = self._timed(ios, load)
        writer.writerow(row_start + [0, "create lazy scans", "success", t_load, None, None,
                         None, io_load, None, None, self._lazy_tables_size_kb()])

        t_transform, io_transform = self._timed(ios, transform)
        writer.writerow(row_start + [-1, "skip lazy transforms", "success", t_transform, None, None,
                         None, io_transform, None, None, self._lazy_tables_size_kb()])

        t_sort, io_sort = self._timed(ios, sort)
        writer.writerow(row_start + [-2, "sort lazy scans", "success", t_sort, None, None,
                         None, io_sort, None, None, self._lazy_tables_size_kb()])

        self.eval_context["exnames"] = exnames
        for name, lf in self._tables.items():
            self.eval_context[name] = lf

    @staticmethod
    def get_table_size(df) -> int | None:
        if isinstance(df, pl.LazyFrame):
            return None
        return QueryExecutorPolarsBase.get_table_size(df)

    def get_table_stats(self) -> dict[str, Any]:
        table_stats_dict: dict[str, Any] = {}
        for name, lf in self._tables.items():
            schema = lf.collect_schema()
            table_stats_dict[name] = {
                "name": name,
                "size (MB)": None,
                "rowCount": None,
                "columnCount": len(schema),
                "columns": [
                    {"name": col, "type": str(dtype)}
                    for col, dtype in schema.items()
                ],
            }
        return table_stats_dict

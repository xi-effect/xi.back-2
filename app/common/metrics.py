import gc
import sys
from collections import Counter
from threading import Lock
from time import monotonic
from typing import ClassVar

from prometheus_client.core import GaugeMetricFamily, Metric
from prometheus_client.registry import Collector


class PythonHeapMetricsCollector(Collector):
    _cache_duration_seconds: ClassVar[int] = 10 * 60
    _most_common_type_count: ClassVar[int] = 30

    def __init__(self) -> None:
        self._lock = Lock()
        self._cached_heap_objects_by_type: dict[str, int] = {}
        self._cached_tracked_objects_count = 0
        self._last_heap_scan_at: float | None = None

    def collect(self) -> list[Metric]:
        with self._lock:
            now = monotonic()

            if (
                self._last_heap_scan_at is None
                or now - self._last_heap_scan_at >= self._cache_duration_seconds
            ):
                tracked_objects = gc.get_objects()
                object_counts_by_type = Counter(
                    type(tracked_object).__name__ for tracked_object in tracked_objects
                )
                common_types = object_counts_by_type.most_common(
                    self._most_common_type_count
                )
                common_types = [
                    (type_name, count)
                    for type_name, count in common_types
                    if type_name != "other"
                ]
                common_type_names = {type_name for type_name, _ in common_types}
                other_count = sum(
                    count
                    for type_name, count in object_counts_by_type.items()
                    if type_name not in common_type_names
                )
                self._cached_heap_objects_by_type = dict(common_types)
                self._cached_heap_objects_by_type["other"] = other_count
                self._cached_tracked_objects_count = len(tracked_objects)
                self._last_heap_scan_at = now

            heap_objects = GaugeMetricFamily(
                "python_heap_objects",
                "Number of objects tracked by the garbage collector, by type.",
                labels=["type"],
            )
            for type_name, object_count in self._cached_heap_objects_by_type.items():
                heap_objects.add_metric([type_name], object_count)

            tracked_objects_metric = GaugeMetricFamily(
                "python_heap_objects_tracked",
                "Number of objects tracked by the Python garbage collector.",
                value=self._cached_tracked_objects_count,
            )
            allocated_blocks_metric = GaugeMetricFamily(
                "python_allocated_blocks",
                "Number of memory blocks currently allocated by the Python interpreter.",
                value=sys.getallocatedblocks(),
            )

            return [
                heap_objects,
                tracked_objects_metric,
                allocated_blocks_metric,
            ]

"""Sampled access detection with refined crossings and local peaks."""
from dataclasses import dataclass
from math import ceil, isfinite


@dataclass(frozen=True)
class Pass:
    start_s: float
    end_s: float
    peak_time_s: float
    peak_elevation_deg: float
    clipped_start: bool
    clipped_end: bool

    @property
    def duration_s(self):
        return self.end_s - self.start_s


def crossing(elevation, threshold, left, right):
    """Bisect a bracketed threshold crossing to within 1 ms."""
    left_above = elevation(left) >= threshold
    while right - left > 0.001:
        mid = (left + right) / 2
        if (elevation(mid) >= threshold) == left_above:
            left = mid
        else:
            right = mid
    return (left + right) / 2


def maximum(elevation, left, right):
    """Refine a bracket around one local maximum, including its endpoints."""
    endpoints = [left, right]
    for _ in range(60):
        a, b = left + (right - left) / 3, right - (right - left) / 3
        if elevation(a) < elevation(b):
            left = a
        else:
            right = b
    return max(endpoints + [(left + right) / 2], key=elevation)


def simulate(elevation, duration_s=86400.0, step_s=10.0, minimum_deg=10.0):
    """Return times, elevations, and nonzero access intervals (elevation >= minimum).

    Detection is sampled: intervals entirely between samples can be missed.
    Refinement improves detected events, but cannot recover unseen intervals.
    """
    if not all(isfinite(v) for v in (duration_s, step_s, minimum_deg)):
        raise ValueError("Simulation inputs must be finite")
    if duration_s <= 0 or step_s <= 0 or not 0 <= minimum_deg <= 90:
        raise ValueError("Duration and step must be positive; minimum must be in [0, 90]")
    count = ceil(duration_s / step_s)
    if count > 2_000_000:
        raise ValueError("Too many samples; increase the sample step")
    times = [min(i * step_s, duration_s) for i in range(count + 1)]
    values = [elevation(t) for t in times]
    above = [v >= minimum_deg for v in values]
    passes = []
    index = 0
    while index < len(times):
        if not above[index]:
            index += 1
            continue
        first = index
        while index + 1 < len(times) and above[index + 1]:
            index += 1
        last = index
        start = times[first] if first == 0 else crossing(elevation, minimum_deg, times[first - 1], times[first])
        end = times[last] if last == count else crossing(elevation, minimum_deg, times[last], times[last + 1])
        candidates = [start, end]
        for k in range(first, last + 1):
            if (k == first or values[k] >= values[k - 1]) and (k == last or values[k] >= values[k + 1]):
                candidates.append(maximum(elevation, max(start, times[max(0, k - 1)]),
                                          min(end, times[min(count, k + 1)])))
        peak = max(candidates, key=elevation)
        if end > start:
            passes.append(Pass(start, end, peak, elevation(peak), first == 0, last == count))
        index += 1
    return times, values, passes

"""Union-based geometric access metrics within one non-periodic time window."""
from math import fsum, isfinite


def merge_intervals(intervals):
    """Merge overlapping or touching (start, end) intervals, without double counting."""
    ordered = sorted(intervals)
    merged = []
    for start, end in ordered:
        if not isfinite(start) or not isfinite(end) or end < start:
            raise ValueError('Intervals must have finite, ordered endpoints')
        if end == start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def access_metrics(intervals, window_s):
    """Measure the union and its complement; never join beginning and ending gaps."""
    if not isfinite(window_s) or window_s <= 0:
        raise ValueError('Window must be finite and positive')
    merged = merge_intervals(intervals)
    if any(start < 0 or end > window_s for start, end in merged):
        raise ValueError('Intervals must lie within the simulation window')
    gaps = []
    cursor = 0.0
    for start, end in merged:
        if start > cursor:
            gaps.append({'start_s': cursor, 'end_s': start, 'duration_s': start - cursor})
        cursor = end
    if cursor < window_s:
        gaps.append({'start_s': cursor, 'end_s': window_s, 'duration_s': window_s - cursor})
    total = fsum(end - start for start, end in merged)
    return {
        'window_s': window_s,
        'interval_count': len(merged),
        'total_access_s': total,
        'access_fraction': total / window_s,
        'access_percent': 100 * total / window_s,
        'longest_gap_s': max((g['duration_s'] for g in gaps), default=0.0),
        'beginning_gap_s': merged[0][0] if merged else window_s,
        'ending_gap_s': window_s - merged[-1][1] if merged else window_s,
        'gaps': gaps,
    }

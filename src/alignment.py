"""Monotone, value-independent alignment with explicit optimal-path ambiguity."""

from itertools import pairwise

from collections import defaultdict
from fractions import Fraction


VERSION = "metadata-order-v2"
MIN_SCORE = 10


def score(p, r):
    """Only location/date/clock metadata enters this score; never angular readings."""
    if p.get("volume", 12) != r.get("volume", 12):
        return None
    pp, rp = p.get("page"), r.get("page")
    if pp is not None and rp is not None:
        gap = abs(pp - rp)
        if gap > 2:
            return None
        value = 8 if gap == 0 else 4 if gap == 1 else 2
    else:
        value = 0
    pd, rd = p.get("date"), r.get("date")
    value += 6 if pd and pd == rd else -6 if pd and rd else -1
    pt, rt = p.get("time_key"), r.get("time_key")
    if pt and rt:
        if pt not in (rt, r.get("time_match_key")):
            return None
        value += 8
    else:
        value -= 2
    return value if value >= MIN_SCORE else None


def optimal_candidates(ps, rs):
    n, m = len(ps), len(rs)
    weights = [[score(p, r) for r in rs] for p in ps]
    forward = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        before, current = forward[i], forward[i + 1]
        for j in range(m):
            value = max(before[j + 1], current[j])
            if weights[i][j] is not None:
                value = max(value, before[j] + weights[i][j])
            current[j + 1] = value
    backward = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        after, current = backward[i + 1], backward[i]
        for j in range(m - 1, -1, -1):
            value = max(after[j], current[j + 1])
            if weights[i][j] is not None:
                value = max(value, after[j + 1] + weights[i][j])
            current[j] = value
    optimum = forward[n][m]
    result = []
    for i in range(n):
        js = [
            j
            for j in range(m)
            if weights[i][j] is not None
            and forward[i][j] + weights[i][j] + backward[i + 1][j + 1] == optimum
        ]
        may_skip = any(forward[i][j] + backward[i + 1][j] == optimum for j in range(m + 1))
        result.append((js, may_skip))
    return result, weights


def compare_records(pafko, extracted, review_links=None):
    from .comparison import audit_conversion, compare_pair, compatible

    review_links = review_links or {}
    pids = {p["id"] for p in pafko}
    r_by_id = {r["id"]: r for r in extracted}
    links = {pid: rid for pid, rid in review_links.items() if pid in pids}
    if len(set(links.values())) != len(links):
        raise ValueError("Reviewed identities must be one to one")
    if any(rid not in r_by_id for rid in links.values()):
        raise ValueError("Reviewed source identity is absent")
    pg, rg = defaultdict(list), defaultdict(list)
    results = {}
    for p in pafko:
        pg[p.get("volume", 12)].append(p)
    for r in extracted:
        rg[r.get("volume", 12)].append(r)
    segments = []
    for volume, ps in pg.items():
        rs = rg[volume]
        positions = {r["id"]: j for j, r in enumerate(rs)}
        anchors = []
        for i, p in enumerate(ps):
            if p["id"] in links:
                if links[p["id"]] not in positions:
                    raise ValueError("Reviewed identity crosses volumes")
                anchors.append((i, positions[links[p["id"]]]))
        if any(b[1] <= a[1] for a, b in pairwise(anchors)):
            raise ValueError("Reviewed identities contradict printed order")
        pi, ri = 0, 0
        for i, j in [*anchors, (len(ps), len(rs))]:
            segments.append((volume, ps[pi:i], rs[ri:j]))
            pi, ri = i + 1, j + 1
    for volume, ps, rs in segments:
        possibilities, weights = optimal_candidates(ps, rs)
        for i, p in enumerate(ps):
            js, may_skip = possibilities[i]
            result = dict(
                pafko_id=p["id"],
                volume=volume,
                page=p.get("page"),
                date=p.get("date"),
                conversion_status=audit_conversion(p),
                source_check="not_reviewed",
                alignment_version=VERSION,
                alignment_basis=None,
                delta_arcsec=None,
                hemisphere_status="unresolved",
                candidate_ids=[rs[j]["id"] for j in js],
                unmatched_optimal_path=may_skip,
            )
            if len(js) == 1 and not may_skip:
                j = js[0]
                r = rs[j]
                basis = "page_date_printed_order"
                if p.get("time_key") and r.get("time_key") and compatible(p, r):
                    count = sum(
                        x.get("time_key") == p["time_key"]
                        and x.get("date") == p.get("date")
                        and x.get("page") == p.get("page")
                        for x in ps
                    )
                    basis = "unique_time" if count == 1 else "time_group_printed_order"
                if p.get("date") != r.get("date"):
                    basis = "page_clock_date_conflict"
                elif p.get("page") != r.get("page"):
                    basis = "date_clock_page_conflict"
                result.update(
                    alignment_basis=basis,
                    alignment_score=weights[i][j],
                    source_role=r.get("role", "observation"),
                    **compare_pair(p, r),
                )
            else:
                result["status"] = "ambiguous" if js else "unmatched"
            results[p["id"]] = result
    for p in pafko:
        if p["id"] in links:
            r = r_by_id[links[p["id"]]]
            results[p["id"]] = dict(
                pafko_id=p["id"],
                volume=p.get("volume", 12),
                page=p.get("page"),
                date=p.get("date"),
                conversion_status=audit_conversion(p),
                source_check="not_reviewed",
                alignment_version=VERSION,
                alignment_basis="source_scan_review",
                candidate_ids=[r["id"]],
                unmatched_optimal_path=False,
                source_role=r.get("role", "observation"),
                **compare_pair(p, r),
            )
        result = results[p["id"]]
        result["numeric_source_sign_status"] = "unresolved"
        result["source_hemisphere_basis"] = None
        if result.get("alignment_basis"):
            r = r_by_id[result["candidate_ids"][0]]
            result["source_hemisphere_basis"] = r.get("hemisphere_basis")
            if p.get("arcsec") is not None and r.get("arcsec") is not None:
                pv, rv = Fraction(p["arcsec"]), Fraction(r["arcsec"])
                if pv and rv:
                    result["numeric_source_sign_status"] = (
                        "consistent" if (pv > 0) == (rv > 0) else "conflict"
                    )
            result.update(
                source_date=r.get("date"),
                source_page=r.get("page"),
                source_time_key=r.get("time_key"),
                date_status="unresolved"
                if not r.get("date")
                else "consistent"
                if p.get("date") == r.get("date")
                else "conflict",
                page_status="unresolved"
                if r.get("page") is None
                else "consistent"
                if p.get("page") == r.get("page")
                else "conflict",
                time_status="unresolved"
                if not p.get("time_key") or not r.get("time_key")
                else "consistent"
                if compatible(p, r)
                else "conflict",
            )
    return [results[p["id"]] for p in pafko]

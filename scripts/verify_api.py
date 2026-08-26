"""Hits the already-running API (e.g. `docker compose up`) over real HTTP and checks the
responses against known values from the actual ingested dataset. No database access, no
app instantiation — just requests against whatever's actually live.

Run: python scripts/verify_api.py
"""

import os
import sys

import requests

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

failures = []


def check(description, condition):
    if condition:
        print(f"  PASS: {description}")
    else:
        print(f"  FAIL: {description}")
        failures.append(description)


def is_json(resp):
    return resp.headers.get("content-type", "").startswith("application/json")


def check_health():
    print("GET /health")
    resp = requests.get(f"{BASE_URL}/health")
    check("status 200", resp.status_code == 200)
    check("body is {'status': 'ok'}", resp.json() == {"status": "ok"})


def check_aggregates_list():
    print("GET /api/v1/aggregates/?day=Monday&period=AM Peak")
    resp = requests.get(
        f"{BASE_URL}/api/v1/aggregates/", params={"day": "Monday", "period": "AM Peak"}
    )
    check("status 200", resp.status_code == 200)
    body = resp.json()
    check("response is a non-empty list", isinstance(body, list) and len(body) > 0)

    match = next((r for r in body if r["link_id"] == 16981048), None)
    check("known link_id 16981048 is present", match is not None)
    if match:
        check("road_name matches known value", match["road_name"] == "Philips Hwy")
        check(
            "average_speed matches known value",
            abs(match["average_speed"] - 45.40133333333333) < 1e-6,
        )
        check("geometry is a LineString", match["geometry"]["type"] == "LineString")


def check_aggregates_bad_day_returns_422():
    print("GET /api/v1/aggregates/?day=Blah&period=AM Peak")
    resp = requests.get(
        f"{BASE_URL}/api/v1/aggregates/", params={"day": "Blah", "period": "AM Peak"}
    )
    check("status 422", resp.status_code == 422)
    check("content-type is JSON", is_json(resp))


def check_aggregate_for_link():
    print("GET /api/v1/aggregates/16981048?day=Monday&period=AM Peak")
    resp = requests.get(
        f"{BASE_URL}/api/v1/aggregates/16981048",
        params={"day": "Monday", "period": "AM Peak"},
    )
    check("status 200", resp.status_code == 200)
    body = resp.json()
    check("link_id matches", body.get("link_id") == 16981048)
    check("road_name matches known value", body.get("road_name") == "Philips Hwy")


def check_aggregate_for_link_no_data_returns_404():
    print("GET /api/v1/aggregates/999999999?day=Monday&period=AM Peak")
    resp = requests.get(
        f"{BASE_URL}/api/v1/aggregates/999999999",
        params={"day": "Monday", "period": "AM Peak"},
    )
    check("status 404", resp.status_code == 404)
    check("content-type is JSON", is_json(resp))


def check_slow_links():
    print("GET /api/v1/patterns/slow_links/?period=AM Peak&threshold=15&min_days=1")
    resp = requests.get(
        f"{BASE_URL}/api/v1/patterns/slow_links/",
        params={"period": "AM Peak", "threshold": 15, "min_days": 1},
    )
    check("status 200", resp.status_code == 200)
    body = resp.json()
    check("response is a list", isinstance(body, list))
    if body:
        sample = body[0]
        check(
            "items have link_id/road_name/slow_day_count",
            {"link_id", "road_name", "slow_day_count"} <= sample.keys(),
        )
        check(
            "every result satisfies min_days=1",
            all(r["slow_day_count"] >= 1 for r in body),
        )


def check_slow_links_bad_min_days_returns_422():
    print("GET /api/v1/patterns/slow_links/?period=AM Peak&threshold=15&min_days=99")
    resp = requests.get(
        f"{BASE_URL}/api/v1/patterns/slow_links/",
        params={"period": "AM Peak", "threshold": 15, "min_days": 99},
    )
    check("status 422 (min_days is capped at 7)", resp.status_code == 422)


def check_spatial_filter():
    print("POST /api/v1/aggregates/spatial_filter/")
    resp = requests.post(
        f"{BASE_URL}/api/v1/aggregates/spatial_filter/",
        json={"day": "Monday", "period": "AM Peak", "bbox": [-81.8, 30.1, -81.6, 30.3]},
    )
    check("status 200", resp.status_code == 200)
    body = resp.json()
    check("response is a non-empty list", isinstance(body, list) and len(body) > 0)
    ids = {r["link_id"] for r in body}
    check("known link_id 16993580 (I-295 S) is present", 16993580 in ids)


def check_spatial_filter_bad_bbox_returns_422():
    print("POST /api/v1/aggregates/spatial_filter/ with malformed bbox")
    resp = requests.post(
        f"{BASE_URL}/api/v1/aggregates/spatial_filter/",
        json={"day": "Monday", "period": "AM Peak", "bbox": [1, 2, 3]},
    )
    check("status 422", resp.status_code == 422)


def check_unmatched_route_returns_json_404():
    print("GET /api/v1/nonexistent/")
    resp = requests.get(f"{BASE_URL}/api/v1/nonexistent/")
    check("status 404", resp.status_code == 404)
    check("content-type is JSON", is_json(resp))


def main():
    checks = [
        check_health,
        check_aggregates_list,
        check_aggregates_bad_day_returns_422,
        check_aggregate_for_link,
        check_aggregate_for_link_no_data_returns_404,
        check_slow_links,
        check_slow_links_bad_min_days_returns_422,
        check_spatial_filter,
        check_spatial_filter_bad_bbox_returns_422,
        check_unmatched_route_returns_json_404,
    ]
    for c in checks:
        c()
        print()

    if failures:
        print(f"{len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print("All checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()

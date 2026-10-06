"""Three API versioning strategies (URL path, header, media type) routed to the same handlers."""
import re

HANDLERS = {
    1: lambda order: {"id": order["id"], "total": order["cents"] / 100},
    2: lambda order: {"id": order["id"], "total": {"amount": order["cents"], "currency": "EUR"}},
}
LATEST = 2


def route(path, headers):
    """Returns (version, strategy). Order: path, custom header, Accept media type, else latest."""
    if m := re.match(r"^/v(\d+)/", path):
        return int(m[1]), "path"
    if v := headers.get("X-Api-Version"):
        return int(v), "header"
    if m := re.search(r"application/vnd\.orders\.v(\d+)\+json", headers.get("Accept", "")):
        return int(m[1]), "media-type"
    return LATEST, "default"


def handle(path, headers, order):
    v, how = route(path, headers)
    if v not in HANDLERS:
        return 406, {"error": f"unsupported version {v}"}, how
    return 200, HANDLERS[v](order), how


def main():
    order = {"id": 7, "cents": 1250}
    cases = [
        (("/v1/orders/7", {}), (200, {"id": 7, "total": 12.5}, "path")),
        (("/orders/7", {"X-Api-Version": "2"}), (200, {"id": 7, "total": {"amount": 1250, "currency": "EUR"}}, "header")),
        (("/orders/7", {"Accept": "application/vnd.orders.v1+json"}), (200, {"id": 7, "total": 12.5}, "media-type")),
        (("/orders/7", {}), (200, {"id": 7, "total": {"amount": 1250, "currency": "EUR"}}, "default")),
        (("/v9/orders/7", {}), (406, {"error": "unsupported version 9"}, "path")),
    ]
    for (path, headers), want in cases:
        got = handle(path, headers, order)
        assert got == want, (path, got)
    print("OK: 5 routing cases; v1 and v2 serve the same order with a breaking total change")


if __name__ == "__main__":
    main()

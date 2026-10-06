"""Feature flags behind an OpenFeature-shaped API: client -> provider, with targeting rules.
The official SDK is not installed; the provider interface below mirrors OpenFeature's
(resolve_boolean_details + evaluation context) so swapping in the SDK is a provider change only."""
import hashlib
from dataclasses import dataclass, field


@dataclass
class Resolution:
    value: object
    reason: str


@dataclass
class InMemoryProvider:
    flags: dict = field(default_factory=dict)

    def resolve_boolean_details(self, key, default, ctx):
        f = self.flags.get(key)
        if f is None:
            return Resolution(default, "ERROR:FLAG_NOT_FOUND")
        if ctx.get("tenant") in f.get("allow_tenants", ()):
            return Resolution(True, "TARGETING_MATCH")
        pct = f.get("rollout_pct")
        if pct is not None:  # sticky bucket: same targeting key always lands in the same bucket
            bucket = int(hashlib.sha256(f"{key}:{ctx.get('targeting_key')}".encode()).hexdigest(), 16) % 100
            return Resolution(bucket < pct, "SPLIT")
        return Resolution(f.get("default", default), "STATIC")


class Client:
    def __init__(self, provider):
        self.provider = provider

    def get_boolean_value(self, key, default, ctx=None):
        return self.provider.resolve_boolean_details(key, default, ctx or {}).value


def main():
    c = Client(InMemoryProvider({
        "new-checkout": {"allow_tenants": ["acme"], "rollout_pct": 30},
        "kill-switch": {"default": False},
    }))
    assert c.get_boolean_value("new-checkout", False, {"tenant": "acme", "targeting_key": "u1"})
    users = [f"user-{i}" for i in range(1000)]
    on = [u for u in users if c.get_boolean_value("new-checkout", False, {"targeting_key": u})]
    assert 240 <= len(on) <= 360, len(on)
    assert on == [u for u in users if c.get_boolean_value("new-checkout", False, {"targeting_key": u})]
    assert c.get_boolean_value("kill-switch", True) is False
    assert c.get_boolean_value("missing", True) is True  # unknown flag falls back to the code default
    print(f"OK: tenant targeting, sticky 30% rollout ({len(on)}/1000), static flag, safe default")


if __name__ == "__main__":
    main()

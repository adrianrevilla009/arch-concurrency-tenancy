"""Token bucket, leaky bucket and sliding-window log compared on the same bursty traffic.
Time is injected, so the run is deterministic and needs no infrastructure."""
from collections import deque


class TokenBucket:
    def __init__(self, rate, burst):
        self.rate, self.burst, self.tokens, self.t = rate, burst, burst, 0.0

    def allow(self, now):
        self.tokens = min(self.burst, self.tokens + (now - self.t) * self.rate)
        self.t = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class LeakyBucket:
    """Meter variant: queue drains at a fixed rate; a full queue rejects."""

    def __init__(self, rate, capacity):
        self.rate, self.capacity, self.level, self.t = rate, capacity, 0.0, 0.0

    def allow(self, now):
        self.level = max(0.0, self.level - (now - self.t) * self.rate)
        self.t = now
        if self.level + 1 <= self.capacity:
            self.level += 1
            return True
        return False


class SlidingWindowLog:
    def __init__(self, limit, window):
        self.limit, self.window, self.log = limit, window, deque()

    def allow(self, now):
        while self.log and self.log[0] <= now - self.window:
            self.log.popleft()
        if len(self.log) < self.limit:
            self.log.append(now)
            return True
        return False


def run(limiter, times):
    return "".join("Y" if limiter.allow(t) else "n" for t in times)


def main():
    times = [0.0] * 10 + [1.0] * 5  # burst of 10 at t=0, another 5 exactly 1s later
    results = {
        "token-bucket (2/s, burst 5)": run(TokenBucket(2, 5), times),
        "leaky-bucket (2/s, cap 5)": run(LeakyBucket(2, 5), times),
        "sliding-log (5 per 1s)": run(SlidingWindowLog(5, 1.0), times),
    }
    for name, r in results.items():
        print(f"{name:30} {r}")
    # all three admit a burst of 5 then reject the rest of the instant burst
    assert all(r[:10] == "YYYYYnnnnn" for r in results.values())
    # after 1s the rate-based limiters refilled only 2 slots; the log forgot the whole burst
    assert results["token-bucket (2/s, burst 5)"][10:] == "YYnnn"
    assert results["leaky-bucket (2/s, cap 5)"][10:] == "YYnnn"
    assert results["sliding-log (5 per 1s)"][10:] == "YYYYY"
    print("OK: same burst handling, different recovery (sliding log allows 2x at the window edge)")


if __name__ == "__main__":
    main()

"""Lease-based leader election on Redis: the leader renews, followers retry, failover on lapse."""
import subprocess, time

KEY, LEASE_MS = "leader", 2000


def redis(*args):
    return subprocess.run(["docker", "exec", "act-leader-redis", "redis-cli", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


class Node:
    def __init__(self, name):
        self.name = name

    def tick(self):
        """Renew if we lead, otherwise try to take the lease. Returns True if leader."""
        if redis("GET", KEY) == self.name:
            redis("PEXPIRE", KEY, str(LEASE_MS))
            return True
        return redis("SET", KEY, self.name, "NX", "PX", str(LEASE_MS)) == "OK"


def main():
    redis("FLUSHALL")
    a, b = Node("a"), Node("b")
    assert a.tick() and not b.tick()
    for _ in range(3):  # a keeps renewing, b stays follower
        time.sleep(0.5)
        assert a.tick() and not b.tick()
    time.sleep(LEASE_MS / 1000 + 0.5)  # a crashes: no more renewals
    assert b.tick(), "b must take over after the lease lapses"
    assert not a.tick(), "a, back from the dead, must not steal leadership"
    print("OK: a led, lease lapsed, b took over, a stayed follower")


if __name__ == "__main__":
    main()

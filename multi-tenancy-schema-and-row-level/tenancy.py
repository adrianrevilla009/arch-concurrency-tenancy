"""Two tenant isolation models on one Postgres: schema-per-tenant and row-level security."""
import subprocess


def psql(sql, user="postgres"):
    r = subprocess.run(["docker", "exec", "-i", "act-tenancy-pg", "psql", "-U", user, "-d", "postgres", "-tAq",
                        "-v", "ON_ERROR_STOP=1", "-c", sql], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


SETUP = """
DROP SCHEMA IF EXISTS tenant_a, tenant_b CASCADE; DROP TABLE IF EXISTS orders;
DROP ROLE IF EXISTS app;
CREATE ROLE app LOGIN;
CREATE SCHEMA tenant_a; CREATE SCHEMA tenant_b;
CREATE TABLE tenant_a.orders (id serial, item text); CREATE TABLE tenant_b.orders (id serial, item text);
INSERT INTO tenant_a.orders(item) VALUES ('a-book'); INSERT INTO tenant_b.orders(item) VALUES ('b-pen');
GRANT USAGE ON SCHEMA tenant_a, tenant_b TO app; GRANT SELECT ON tenant_a.orders, tenant_b.orders TO app;
CREATE TABLE orders (id serial, tenant text NOT NULL, item text);
INSERT INTO orders(tenant, item) VALUES ('a', 'a-book'), ('b', 'b-pen');
GRANT SELECT ON orders TO app;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY by_tenant ON orders USING (tenant = current_setting('app.tenant', true));
"""


def main():
    psql(SETUP)
    # 1) schema-per-tenant: search_path selects the tenant, other schemas are not reachable by name resolution
    for t, want in (("tenant_a", "a-book"), ("tenant_b", "b-pen")):
        assert psql(f"SET search_path={t}; SELECT item FROM orders", "app") == want
    # 2) row-level security: same table, the policy filters by a per-session setting
    for t, want in (("a", "a-book"), ("b", "b-pen")):
        assert psql(f"SET app.tenant='{t}'; SELECT string_agg(item, ',') FROM orders", "app") == want
    # fail-closed: no tenant set means no rows
    assert psql("SELECT count(*) FROM orders", "app") == "0"
    # table owner bypasses RLS unless FORCE is set: why the app must not connect as owner
    assert psql("SELECT count(*) FROM orders") == "2"
    print("OK: schema isolation, RLS isolation, fail-closed default, owner bypass shown")


if __name__ == "__main__":
    main()

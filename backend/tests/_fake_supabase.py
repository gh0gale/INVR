"""In-memory stand-in for the supabase-py query builder, covering only the calls
the horizons and profile routes make."""

PRIMARY_KEYS = {"user_profiles": ("id",), "stock_horizons": ("user_id", "ticker")}


class _Result:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, db, table):
        self.db, self.table = db, table
        self.filters, self.op, self.payload = [], "select", None

    def select(self, *_):
        self.op = "select"
        return self

    def eq(self, col, val):
        self.filters.append((col, val))
        return self

    def update(self, changes):
        self.op, self.payload = "update", changes
        return self

    def upsert(self, row):
        self.op, self.payload = "upsert", row
        return self

    def _match(self, row):
        return all(row.get(c) == v for c, v in self.filters)

    def execute(self):
        rows = self.db.tables.setdefault(self.table, [])
        if self.op == "select":
            return _Result([dict(r) for r in rows if self._match(r)])
        if self.op == "update":
            hit = [r for r in rows if self._match(r)]
            for r in hit:
                r.update(self.payload)
            return _Result([dict(r) for r in hit])
        if self.op == "upsert":
            keys = PRIMARY_KEYS[self.table]
            for r in rows:
                if all(r.get(k) == self.payload[k] for k in keys):
                    r.update(self.payload)
                    return _Result([dict(r)])
            rows.append(dict(self.payload))
            return _Result([dict(self.payload)])
        raise AssertionError(self.op)


class FakeSupabase:
    def __init__(self):
        self.tables: dict[str, list[dict]] = {}

    def table(self, name):
        return _Query(self, name)

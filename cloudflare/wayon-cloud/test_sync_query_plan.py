"""SQLite cursor correctness/scan regression tests, with no production access."""
import sqlite3
import unittest
from pathlib import Path


class SyncQueryPlanTest(unittest.TestCase):
  def setUp(self):
    self.db = sqlite3.connect(":memory:")
    for table, column in (("trips", "created_at"), ("snapshots", "created_at"),
                          ("impact_events", "received_at")):
      self.db.execute(f"CREATE TABLE {table}(id TEXT PRIMARY KEY, device_id TEXT, {column} TEXT NOT NULL)")
      self.db.executemany(f"INSERT INTO {table} VALUES (?, ?, ?)", [
        (f"{i:06d}", f"vehicle-{i % 5}", f"2026-09-10T00:{i // 1000:02d}:00Z")
        for i in range(10000)
      ])

  def tearDown(self):
    self.db.close()

  def migrate(self):
    self.db.executescript((Path(__file__).parent / "migrations/0009_sync_cursor_indexes.sql").read_text())

  def test_pagination_keeps_equal_timestamps_and_all_five_devices(self):
    self.migrate()
    self.migrate()  # Safe to apply twice.
    for table, column in (("trips", "created_at"), ("snapshots", "created_at"),
                          ("impact_events", "received_at")):
      cursor = ("", "")
      received = []
      while True:
        rows = self.db.execute(
          f"SELECT {column}, id, device_id FROM {table} WHERE ({column}, id) > (?, ?) "
          f"ORDER BY {column}, id LIMIT 101", cursor,
        ).fetchall()
        page = rows[:100]
        if not page:
          break
        received.extend(page)
        cursor = page[-1][:2]
        if len(rows) <= 100:
          break
      self.assertEqual(len(received), 10000)
      self.assertEqual(len({row[1] for row in received}), 10000)
      self.assertEqual({row[2] for row in received}, {f"vehicle-{i}" for i in range(5)})

  def test_idle_sync_seeks_instead_of_scanning_accumulated_history(self):
    def instructions(sql, args):
      count = 0

      def step():
        nonlocal count
        count += 1
        return 0

      self.db.set_progress_handler(step, 1)
      result = self.db.execute(sql, args).fetchall()
      self.db.set_progress_handler(None, 0)
      self.assertEqual(result, [])
      return count

    stamp, ident = "2026-09-10T00:09:00Z", "009999"
    old = instructions("SELECT * FROM trips WHERE created_at > ? OR (created_at = ? AND id > ?) "
                       "ORDER BY created_at, id LIMIT 101", (stamp, stamp, ident))
    self.migrate()
    for table, column in (("trips", "created_at"), ("snapshots", "created_at"),
                          ("impact_events", "received_at")):
      sql = f"SELECT * FROM {table} WHERE ({column}, id) > (?, ?) ORDER BY {column}, id LIMIT 101"
      plan = " ".join(str(r) for r in self.db.execute("EXPLAIN QUERY PLAN " + sql, (stamp, ident)))
      self.assertIn("SEARCH", plan)
      self.assertNotIn("TEMP B-TREE", plan)
      new = instructions(sql, (stamp, ident))
      self.assertLess(new, old // 100)
      print(f"{table}: idle sync SQLite VM steps {old} -> {new} (not D1 billed rows)")


if __name__ == "__main__":
  unittest.main()

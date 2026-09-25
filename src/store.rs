use rusqlite::{Connection, OptionalExtension};

pub struct Store {
    conn: Connection,
}

impl Store {
    pub fn new() -> Result<Self, ()> {
        let conn = Connection::open("store.db").map_err(|_| ())?;
        conn.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)", []).map_err(|_| ())?;
        Ok(Self { conn })
    }

    pub fn get(&self, key: &str) -> Result<String, ()> {
        self.conn
            .query_row("SELECT value FROM kv WHERE key = ?1", [key], |row| row.get::<_, String>(0))
            .optional()
            .map_err(|_| ())?
            .ok_or(())
    }

    pub fn set(&self, key: &str, value: &str) -> Result<(), ()> {
        self.conn
            .execute(
                "INSERT INTO kv (key, value) VALUES (?1, ?2)
             ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
            .map(|_| ())
            .map_err(|_| ())
    }

    pub fn del(&self, key: &str) -> Result<(), ()> {
        self.conn.execute("DELETE FROM kv WHERE key = ?1", [key]).map(|_| ()).map_err(|_| ())
    }

    pub fn list(&self, pattern: &str, cursor: i64, limit: i64) -> Result<Vec<String>, ()> {
        let mut stmt = self.conn.prepare("SELECT key FROM kv WHERE key GLOB ?1 ORDER BY key LIMIT ?2 OFFSET ?3").map_err(|_| ())?;
        let rows = stmt.query_map(rusqlite::params![pattern, limit, cursor], |r| r.get::<_, String>(0)).map_err(|_| ())?;
        let mut out = Vec::new();
        for r in rows {
            out.push(r.map_err(|_| ())?);
        }
        Ok(out)
    }
}

static GLOBAL_STORE: std::sync::OnceLock<tokio::sync::Mutex<Store>> = std::sync::OnceLock::new();

pub fn store() -> &'static tokio::sync::Mutex<Store> {
    GLOBAL_STORE.get_or_init(|| {
        tokio::sync::Mutex::new(Store::new().unwrap())
    })
}


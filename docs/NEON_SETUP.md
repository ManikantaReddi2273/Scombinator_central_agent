# Neon Database Setup (S Combinator)

Use **Neon** instead of Render Postgres for `DATABASE_URL`.

## 1. Connection strings

From Neon dashboard → Connection string (pooled):

**Sync / Render env (`DATABASE_URL`):**
```text
postgresql://neondb_owner:PASSWORD@HOST-pooler...neon.tech/neondb?sslmode=require
```

**Local `backend/.env` (already set if you followed agent setup):**
```env
DATABASE_URL=postgresql+asyncpg://neondb_owner:PASSWORD@HOST-pooler...neon.tech/neondb?ssl=require
DATABASE_URL_SYNC=postgresql://neondb_owner:PASSWORD@HOST-pooler...neon.tech/neondb?sslmode=require
LANGRAPH_CHECKPOINT_DB_URL=<same as DATABASE_URL>
```

Do **not** put passwords in git. `.env` is gitignored.

## 2. Create tables on Neon

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python init_db.py
```

Or on Render: redeploy backend — `start_render.sh` runs `init_db.py` on boot.

## 3. Point Render backend at Neon

1. Render → **scombinator-backend** → **Environment**
2. Set / edit **`DATABASE_URL`** to the Neon **postgresql://** URL (`sslmode=require`)
3. Remove any old Render-Postgres-linked `DATABASE_URL` if still present
4. **Manual Deploy** the backend
5. After it is healthy, you may **delete** the Render resource **scombinator-db** (optional)

Blueprint `render.yaml` no longer creates `scombinator-db`; `DATABASE_URL` is `sync: false` (you paste Neon).

## 4. Security note

If a Neon password was shared in chat, **rotate it** in Neon → Reset password, then update `.env` + Render env.

## 5. Data migration (optional)

Switching to empty Neon does **not** copy old Render data. To migrate:

```bash
pg_dump "OLD_RENDER_URL" --no-owner --no-acl -Fc -f backup.dump
pg_restore --no-owner --no-acl -d "NEON_URL" backup.dump
```

Then skip `init_db` create if tables already restored (admin may already exist).

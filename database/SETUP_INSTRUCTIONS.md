# Supabase Database Setup Instructions

## Step 1: Create New Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Fill in:
   - **Name**: `prophecy` (or your choice)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to you
   - **Pricing Plan**: Free tier is fine for development
4. Click "Create new project"
5. Wait 2-3 minutes for project to be provisioned

## Step 2: Get Your Credentials

Once your project is ready:

1. Go to **Project Settings** (gear icon in sidebar)
2. Go to **API** section
3. Copy these values:

   ```
   Project URL: https://xxxxx.supabase.co
   anon/public key: eyJhbG...
   service_role key: eyJhbG... (keep this secret!)
   ```

4. Go to **Database** section
5. Scroll down to "Connection string" → "URI"
6. Copy the connection string (it looks like):
   ```
   postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ```
7. **Important**: Replace `[YOUR-PASSWORD]` with the database password you created

## Step 3: Update Backend .env File

Open `backend/.env` and fill in:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbG...
SUPABASE_SERVICE_KEY=eyJhbG...
DATABASE_URL=postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

## Step 4: Run Database Schema

1. In Supabase Dashboard, go to **SQL Editor** (in sidebar)
2. Click "New query"
3. Copy the **entire contents** of `database/schema.sql`
4. Paste into the SQL editor
5. Click **"Run"** (or press Cmd/Ctrl + Enter)
6. You should see: "Success. No rows returned"

## Step 5: Verify Tables Created

1. Go to **Table Editor** (in sidebar)
2. You should see all tables:
   - users
   - rooms
   - memberships
   - markets
   - trades
   - resolution_votes
   - prophet_bets
   - anomaly_flags
   - narrative_events
   - whispers
   - achievements

3. Click on "users" table
4. You should see 1 row: **Prophet** user (the AI agent)

## Step 6: Enable Realtime (Optional for now)

For live updates later:

1. Go to **Database** → **Replication**
2. Enable replication for these tables:
   - markets
   - trades
   - narrative_events
   - resolution_votes

## ✅ Setup Complete!

Your Supabase database is ready. Return to backend and run:

```bash
cd backend
source venv/bin/activate
python tests/test_step2.py
```

This will verify the database connection works.

## Troubleshooting

**"Failed to connect":**
- Check DATABASE_URL is correct
- Make sure you replaced [YOUR-PASSWORD] with actual password
- Check your IP is allowed (Supabase allows all IPs by default)

**"Relation does not exist":**
- Make sure you ran the full schema.sql in SQL Editor
- Check for any errors in the SQL execution

**"Extension uuid-ossp does not exist":**
- Supabase should have this by default
- Try running just: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`

# Hermes Backend API — 3 Apps

A **monorepo** with three independent Node.js services sharing a PostgreSQL database via Prisma.

```
┌──────────────────────────────────────────────────┐
│                Firebase Auth                      │
│  (ID tokens from client → verified by all apps)   │
└────┬────────────┬────────────────┬───────────────┘
     │            │                │
     ▼            ▼                ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Auth     │ │ Core     │ │ Billing      │
│ Service  │ │ Service  │ │ Service      │
│ :4001    │ │ :4002    │ │ :4003        │
│          │ │          │ │              │
│ • sync   │ │ • contacts│ │ • Stripe     │
│ • /me    │ │ • files   │ │   checkout   │
│ • welcome│ │ • AI      │ │ • webhooks  │
│   email  │ │   summary │ │ • subs      │
└────┬─────┘ └────┬─────┘ └──────┬───────┘
     │            │               │
     └────────────┼───────────────┘
                  ▼
         ┌────────────────┐
         │  PostgreSQL     │
         │  (Prisma ORM)   │
         └────────────────┘
```

---

## 🔧 Stack

| Layer         | Choice                                |
|--------------|---------------------------------------|
| Runtime       | Node.js 20+                           |
| Framework     | Express.js                            |
| Database      | PostgreSQL 16 + Prisma ORM            |
| Auth          | Firebase Admin SDK (ID token verify)  |
| Email         | Resend                                |
| File storage  | Firebase Storage                      |
| AI            | Mistral AI API                        |
| Payments      | Stripe                                |

---

## 🚀 Quick Start

### 1. PostgreSQL

```bash
cd backend
docker compose up -d          # starts postgres on :5432
```

Or point `DATABASE_URL` at any running PostgreSQL instance.

### 2. Environment variables

```bash
cp .env.example .env
# Fill in your real keys (see .env.example for all fields)
```

**Required variables:**

| Variable                   | Where to get it                           |
|---------------------------|-------------------------------------------|
| `DATABASE_URL`            | Your PostgreSQL connection string         |
| `FIREBASE_PROJECT_ID`     | Firebase Console → Project Settings       |
| `FIREBASE_CLIENT_EMAIL`   | Firebase → Service Accounts → JSON key    |
| `FIREBASE_PRIVATE_KEY`    | Firebase → Service Accounts → JSON key    |
| `FIREBASE_STORAGE_BUCKET` | Firebase → Storage → bucket name          |
| `RESEND_API_KEY`          | https://resend.com/api-keys               |
| `STRIPE_SECRET_KEY`       | https://dashboard.stripe.com/apikeys      |
| `STRIPE_WEBHOOK_SECRET`   | Stripe CLI `stripe listen --forward-to ...` |
| `MISTRAL_API_KEY`         | https://console.mistral.ai/api-keys/      |

### 3. Install & generate Prisma client

```bash
npm install
npm run db:push    # pushes schema to PostgreSQL (migration-free for dev)
```

### 4. Run all 3 services

```bash
npm run dev
```

Or run them individually in separate terminals:

```bash
npm run dev:auth
npm run dev:core
npm run dev:billing
```

---

## 📡 API Reference

### Auth Service (`localhost:4001`)

| Method | Path             | Auth | Description                              |
|--------|------------------|------|------------------------------------------|
| POST   | `/api/auth/sync` | 🔑   | Sync Firebase user → create local user + send welcome email |
| GET    | `/api/auth/me`   | 🔑   | Get current user profile                 |
| GET    | `/health`        | —    | Health check                             |

### Core Service (`localhost:4002`)

**Contacts**

| Method | Path                        | Auth | Description                    |
|--------|-----------------------------|------|--------------------------------|
| GET    | `/api/contacts`             | 🔑   | List contacts (paginated)      |
| GET    | `/api/contacts/:id`        | 🔑   | Get single contact             |
| POST   | `/api/contacts`             | 🔑   | Create contact (auto-tagged via AI) |
| PATCH  | `/api/contacts/:id`        | 🔑   | Update contact                 |
| DELETE | `/api/contacts/:id`        | 🔑   | Delete contact                 |
| POST   | `/api/contacts/:id/summarise` | 🔑 | Summarise contact via Mistral  |

**Files**

| Method | Path                  | Auth | Description                           |
|--------|-----------------------|------|---------------------------------------|
| GET    | `/api/files`          | 🔑   | List user's files                     |
| POST   | `/api/files/upload`   | 🔑   | Upload file (→ Firebase Storage + AI) |
| DELETE | `/api/files/:id`     | 🔑   | Delete file                           |

**AI**

| Method | Path              | Auth | Description                  |
|--------|-------------------|------|------------------------------|
| POST   | `/api/ai/summarise` | 🔑 | Summarise arbitrary text     |
| POST   | `/api/ai/tags`    | 🔑   | Generate tags from text      |

### Billing Service (`localhost:4003`)

| Method | Path                             | Auth | Description                     |
|--------|----------------------------------|------|---------------------------------|
| POST   | `/api/billing/create-checkout`   | 🔑   | Create Stripe checkout session  |
| GET    | `/api/billing/subscription`      | 🔑   | Get current subscription        |
| GET    | `/api/billing/invoices`          | 🔑   | Invoice history                 |
| POST   | `/api/billing/webhook`           | —    | Stripe webhook (raw body)       |
| GET    | `/health`                        | —    | Health check                    |

> 🔑 = requires `Authorization: Bearer <Firebase ID Token>` header

---

## 📁 Project Structure

```
backend/
├── apps/
│   ├── auth-service/           # Firebase auth + user sync
│   │   └── src/
│   │       ├── index.js
│   │       ├── middleware/
│   │       │   └── firebaseAuth.js
│   │       ├── routes/
│   │       │   └── users.js
│   │       └── services/
│   │           └── emailService.js
│   ├── core-service/           # Contacts + Files + AI
│   │   └── src/
│   │       ├── index.js
│   │       ├── middleware/
│   │       │   └── firebaseAuth.js
│   │       ├── routes/
│   │       │   ├── contacts.js
│   │       │   ├── files.js
│   │       │   └── ai.js
│   │       └── services/
│   │           ├── storageService.js
│   │           └── aiService.js
│   └── billing-service/        # Stripe payments
│       └── src/
│           ├── index.js
│           ├── middleware/
│           │   └── firebaseAuth.js
│           ├── routes/
│           │   ├── payments.js
│           │   └── webhooks.js
│           └── services/
│               └── stripeService.js
├── packages/
│   └── prisma/                 # Shared Prisma schema + client
│       ├── index.js
│       ├── schema.prisma
│       └── package.json
├── docker-compose.yml
├── .env.example
├── .gitignore
└── package.json                # npm workspaces root
```

---

## 📦 Prisma Scripts

```bash
npm run db:generate   # Regenerate Prisma client after schema change
npm run db:push       # Push schema to DB (dev, no migrations)
npm run db:migrate    # Create a new migration
npm run db:studio     # Open Prisma Studio (GUI for data)
```

---

## 🌐 Client Usage (Frontend)

Every request (except the webhook) needs a Firebase ID token in the header:

```js
const idToken = await firebase.auth().currentUser.getIdToken();

await fetch("http://localhost:4002/api/contacts", {
  headers: { Authorization: `Bearer ${idToken}` },
});
```

**Sign-up flow:**

1. User signs up via Firebase Auth on the client
2. Client calls `POST /api/auth/sync` with the Firebase token
3. Auth-service creates the local user record and sends a welcome email via Resend
4. Client can now use Core and Billing services

---

## 🧪 Stripe Webhooks (Local Dev)

```bash
# Install Stripe CLI, then:
stripe listen --forward-to localhost:4003/api/billing/webhook

# Copy the webhook signing secret into your .env as STRIPE_WEBHOOK_SECRET
```

---

## ⚡ File: `/home/studi/backend/.env.example` — copy to `.env`, fill in values

```env
DATABASE_URL="postgresql://hermes:hermes_dev_pass@localhost:5432/hermes_backend"
AUTH_SERVICE_PORT=4001
CORE_SERVICE_PORT=4002
BILLING_SERVICE_PORT=4003
# ... plus all the keys listed in .env.example
```
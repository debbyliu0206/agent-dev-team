# Technical Decision Catalog

Production-grade, industry-standard options to present to a non-technical user. For each decision,
offer 2–3 of these, give the plain-English pros/cons, optionally mark one "(Recommended)" with a
reason tied to the user's goal — then let the user choose.

> ⚠️ **Version numbers go stale fast.** Where specific products/models are named, treat them as
> *examples of the category*, not a current recommendation. For LLMs especially, choose a
> *provider/family* here and verify the exact current model at build time
> (`/google-agents-cli-workflow` → model listing command). Do not pin a model version from memory.

---

### App Type
1. **Web application (SPA / SSR)** — *Pros:* reachable anywhere via URL, instant updates, huge ecosystem. *Cons:* needs a connection, limited access to native device hardware.
2. **Mobile app (iOS / Android)** — *Pros:* native performance, offline use, push notifications, app-store distribution. *Cons:* higher cost, app-store review.
3. **CLI / agent tool** — *Pros:* fast to build, ideal for automation and developer workflows. *Cons:* no GUI, audience limited to technical/power users.

### Frontend Framework
1. **Next.js (React)** — *Pros:* great SEO, fast loads via SSR, built-in API routes, strong default for most web apps. *Cons:* steeper curve than plain React, more deployment moving parts.
2. **React (SPA)** — *Pros:* industry standard, vast component ecosystem, great for highly interactive UIs. *Cons:* you wire up routing/state yourself, overkill for simple sites.
3. **Plain HTML/CSS/JS** — *Pros:* zero dependencies, maximum simplicity and performance. *Cons:* hard to scale for complex, state-heavy apps.

### Backend Language / Framework
1. **Python (FastAPI)** — *Pros:* the standard for AI/ML/agent work, readable, rapid to build. *Cons:* slower raw execution than Go/Node.
2. **Node.js (Express / Fastify)** — *Pros:* same language as the frontend, huge npm ecosystem. *Cons:* single-threaded; struggles with heavy CPU-bound work.
3. **Go** — *Pros:* excellent performance, great concurrency, ships as one binary. *Cons:* stricter/more verbose, smaller web-rapid-tooling ecosystem.

### Database
1. **PostgreSQL (relational/SQL)** — *Pros:* rock-solid, powerful queries, enforces data integrity. Managed options: Cloud SQL, Supabase. *Cons:* needs an upfront schema, harder to shard horizontally.
2. **Document store (Firestore / MongoDB, NoSQL)** — *Pros:* flexible JSON schema, fast iteration, easy horizontal scale. *Cons:* joins/complex queries are awkward; easy to make a mess without discipline.
3. **Redis (in-memory)** — *Pros:* extremely fast, ideal for caching/sessions/queues. *Cons:* not your primary durable store (typically ephemeral). Usually paired with #1 or #2, not used alone.

### Authentication
1. **Managed auth (Firebase Auth / Supabase Auth / Clerk)** — *Pros:* drop-in UI, social logins, fast to ship. *Cons:* some vendor lock-in; user migration later takes effort.
2. **Auth0** — *Pros:* enterprise-grade, highly configurable, dedicated identity platform. *Cons:* costs grow at scale; configuration heavy for simple apps.
3. **Self-managed (e.g. Auth.js/NextAuth)** — *Pros:* open-source, free, you own the user data. *Cons:* you run the tables/security yourself; more responsibility.

### Hosting & Deployment
1. **Google Cloud Run** — *Pros:* scales to zero, runs any container, pay-per-use; native fit for agents-cli deploys. *Cons:* needs a Dockerfile + basic cloud knowledge.
2. **Vercel / Netlify** — *Pros:* zero-config frontend/Next.js deploys, automatic PR previews. *Cons:* pricey for high bandwidth or long-running backends.
3. **Render / Railway** — *Pros:* simple "git push to deploy" for backends (Node/Python). *Cons:* less control than raw cloud; costs ramp with scale.

### API Style
1. **REST** — *Pros:* universally understood, simple HTTP verbs, easy to cache. *Cons:* can over/under-fetch on complex screens.
2. **GraphQL** — *Pros:* client fetches exactly what it needs, single endpoint, strongly typed. *Cons:* harder network caching, more setup to secure.

### LLM Provider / Family
*(Pick a family; verify the current model at build time — see warning above.)*
1. **Anthropic Claude** — *Pros:* strong reasoning and coding, long context, good instruction-following. *Cons:* different API shape if migrating from another provider.
2. **Google Gemini** — *Pros:* very large context, native multimodal (image/audio/video), tight GCP/ADK integration. *Cons:* API differs from OpenAI-style SDKs.
3. **OpenAI GPT** — *Pros:* broad ecosystem/tooling, widely documented. *Cons:* cost/latency vary by model tier.

### Secrets / Env-Var Management
1. **Cloud secret manager (Google Secret Manager / AWS Secrets Manager)** — *Pros:* access control, versioning, audit; production standard. *Cons:* needs cloud SDK + IAM setup.
2. **Platform env vars (Cloud Run / Vercel / Render dashboard)** — *Pros:* easy, injected at runtime. *Cons:* tied to that platform; still need a local-dev story.
3. **`.env` file (local/dev only)** — *Pros:* simplest for local development. *Cons:* easy to leak to git; not for production. Pair with #1 or #2 for deployed environments.

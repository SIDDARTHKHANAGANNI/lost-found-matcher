# Lost & Found Matcher

A full-stack lost-and-found platform built for RV University, combining computer vision, vector search, and human-verified claims to help students recover lost items — and prevent false claims on found ones.

## The problem

Campus lost-and-found boards are unstructured and slow: a lost backpack posted in one WhatsApp group might never reach the person who found it in another. And when someone does claim an item, there's usually no way to verify they actually own it.

This project solves both — automated matching for people who have a photo, manual search for people who don't, and a proof-based claim system so items only go to their real owners.

## How it works

1. **Post an item** — lost or found, with a photo, category, description, and location.
2. **CLIP generates an embedding** — a 512-dimensional vector combining visual features (70%) and text description (30%), using OpenAI's CLIP model.
3. **Automated matching** — the new item is compared against the opposite pool (lost items search found items, and vice versa) using cosine similarity search in PostgreSQL via pgvector, pre-filtered by category.
4. **Multi-signal ranking** — raw visual/semantic similarity is blended with location proximity and time-decay scoring to break ties between visually identical items (e.g. two black JanSport backpacks).
5. **No photo? Browse manually** — a filterable search page lets users scan found items by category, location, or keyword without needing an image.
6. **Claim with proof** — anyone who thinks an item is theirs submits an identifying detail only the real owner would know. The finder reviews and approves or rejects it.
7. **Contact exchange** — once a claim is approved, the claimant can retrieve the finder's contact email to arrange pickup. Contact info is never exposed before approval.
8. **Activity tracking** — users can see the status of everything they've posted and every claim they've submitted, in one place.

## Tech stack

**Backend**
- FastAPI (Python)
- PostgreSQL with pgvector extension (hosted on Neon)
- SQLAlchemy ORM
- CLIP (`openai/clip-vit-base-patch32`) via Hugging Face Transformers, for image + text embeddings
- JWT authentication with bcrypt password hashing
- Pytest for unit tests
- Docker (CPU-only PyTorch build)

**Frontend**
- Plain HTML, CSS, and JavaScript — no framework, no build step
- Directly consumes the FastAPI backend via `fetch`

## Core engineering decisions

- **Hybrid embeddings over pure image matching.** Generic items (a plain black backpack, a steel water bottle) look nearly identical to a vision model. Blending image embeddings with text-description embeddings gives the matcher more to work with than pixels alone.
- **Location + time as tiebreakers, not primary signals.** Visual similarity dominates the final score (70%), with location proximity (20%) and time decay (10%) used to separate otherwise-identical candidates — e.g. a backpack lost near the library ranks above a visually similar one reported across campus.
- **Claims are never auto-approved.** The system narrows candidates and ranks them, but final ownership verification is always a human decision by the finder, based on identifying proof from the claimant. This was a deliberate choice to prevent the system from being used to take items that aren't the claimant's.
- **Connection pool resilience.** Neon (serverless Postgres) drops idle connections; the app uses `pool_pre_ping` and `pool_recycle` to transparently reconnect rather than surfacing intermittent 500 errors to users.

## Project structure

```
lost-found-matcher/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── config.py
│   │   ├── auth.py
│   │   ├── init_db.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   └── items.py
│   │   └── services/
│   │       ├── embedding.py      # CLIP inference
│   │       ├── matching.py       # similarity search + ranking
│   │       └── location.py       # location proximity scoring
│   ├── tests/
│   │   ├── test_embedding.py
│   │   └── test_matching.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── login.html
│   ├── signup.html
│   ├── index.html          # post an item
│   ├── browse.html         # manual search
│   ├── matches.html        # auto-matched results
│   ├── claims.html         # review claims on your items
│   ├── activity.html       # status of your posts + submitted claims
│   ├── css/style.css
│   └── js/api.js
└── docker-compose.yml
```

## Running locally

**Backend**
```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
cp .env.example .env              # then fill in DATABASE_URL, SECRET_KEY
python -m app.init_db
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
python -m http.server 5500
```

Open `http://localhost:5500/login.html`.

**Or, run the backend in Docker:**
```bash
docker build -t lost-found-backend ./backend
docker run -p 8000:8000 --env-file backend/.env lost-found-backend
```

## Testing

```bash
cd backend
pytest tests/ -v
```

Covers CLIP embedding output shape/determinism and the location/time scoring logic used in match ranking.

## Known limitations / future work

- **Contact is email-only** — no in-app messaging yet. Reasonable as a v1, but a real chat flow would be smoother.
- **Local file storage** — uploaded images are stored on the server's local filesystem, which doesn't persist across container redeploys. Would move to S3-compatible object storage (e.g. Cloudflare R2) for production use.
- **No rate limiting or upload validation yet** — needed before wider public rollout to prevent spam or abuse.
- **No real-time notifications** — match/claim status updates require checking the Activity page rather than getting pushed to the user.

## Author

Built by Siddarth K, CSE @ RV University.
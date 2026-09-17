# Task Panel

A team task tracker: tasks with checklists, attachments, comments with @mentions and notifications, an audit log, and team statistics — built as a server-rendered Django site.

## Technology

- **Backend:** Django 5 (Python), classic server-rendered views/templates — no separate REST API.
- **Database:** PostgreSQL 16.
- **Frontend:** [htmx](https://htmx.org) for dynamic interactions (modals, filters, live checklist/comments) plus a small amount of vanilla JavaScript — no SPA framework, no build step. Styling is a single custom CSS file (no Tailwind/Bootstrap), fonts via Google Fonts.
- **Auth:** Django's built-in session authentication. Roles (`admin` / `member`) are stored on a `Person` model, not Django's permission system.
- **Infrastructure:** Docker Compose with two services — `db` (Postgres) and `web` (Django dev server).

## Installation

Requires [Docker](https://www.docker.com/) with Docker Compose. No Python/pip setup needed on your machine either way — everything runs inside containers.

### Recommended: load the pre-built images (no network calls for dependencies at all)

Use this if you were handed an image bundle (`taskpanel-all-images.tar.gz`) alongside this repo — it contains both the `web` app image and the exact `postgres:16` image already built, so **nothing gets downloaded or compiled on your machine**, sidestepping any corporate proxy/antivirus HTTPS interception issues entirely.

1. Clone the repository and enter it:
   ```bash
   git clone <repo-url>
   cd Task_manager
   ```
2. Load the images from the bundle you were given (adjust the path to wherever you saved it):
   ```bash
   docker load -i taskpanel-all-images.tar.gz
   ```
3. Start the containers — **no `--build`**, the images already exist locally:
   ```bash
   docker compose up -d
   ```
4. Open [http://localhost:8000](http://localhost:8000) and sign in with one of the seeded demo accounts (or your own, once created via the admin's **Add person** button):

   | Username | Password | Role |
   |---|---|---|
   | `jblake` | `Harbor42Kite` | Admin |
   | `mchen` | `Violet9Stream` | Member |

   These are created automatically on first startup by a migration that seeds sample tasks on a fresh, empty database — it never touches or resets real data added afterwards.

### Alternative: build from source

If you weren't given an image bundle, or want to build from the current source instead:
```bash
docker compose up -d --build
```
This downloads the Python base image and installs dependencies via `pip`. If it fails with `CERTIFICATE_VERIFY_FAILED`, that means something on your machine (a corporate proxy or antivirus with HTTPS inspection) is intercepting the connection to PyPI — `pip` doesn't trust that interception certificate even if the rest of your system does, and it's not fixable from inside the image. Use the pre-built image bundle above instead — it needs no PyPI or Docker Hub access at all.

### Useful commands

```bash
docker compose logs -f web       # follow the app logs
docker compose exec web python manage.py createsuperuser   # create an extra Django admin account
docker compose down              # stop the containers (keeps data)
docker compose down -v           # stop and wipe the database completely
```

## Inspecting the database

Credentials are the `POSTGRES_*` values in your `.env` file (`taskpanel` / `change-me` by default — check your actual `.env`, it may have been regenerated).

**Option A — psql inside the container, no extra tooling needed:**
```bash
docker compose exec db psql -U taskpanel -d taskpanel
```

**Option B — any external client (DBeaver, TablePlus, pgAdmin, etc.):**
The `db` service publishes its port to the host, so connect to:
- Host: `localhost`
- Port: `5432`
- Database / User / Password: the `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` values from `.env`

**Option C — Django admin (read/write UI, no SQL):**
```bash
docker compose exec web python manage.py createsuperuser
```
Then open [http://localhost:8000/admin](http://localhost:8000/admin) and log in with that account.

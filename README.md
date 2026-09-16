# Task Panel

A team task tracker: tasks with checklists, attachments, comments with @mentions and notifications, an audit log, and team statistics — built as a server-rendered Django site.

## Technology

- **Backend:** Django 5 (Python), classic server-rendered views/templates — no separate REST API.
- **Database:** PostgreSQL 16.
- **Frontend:** [htmx](https://htmx.org) for dynamic interactions (modals, filters, live checklist/comments) plus a small amount of vanilla JavaScript — no SPA framework, no build step. Styling is a single custom CSS file (no Tailwind/Bootstrap), fonts via Google Fonts.
- **Auth:** Django's built-in session authentication. Roles (`admin` / `member`) are stored on a `Person` model, not Django's permission system.
- **Infrastructure:** Docker Compose with two services — `db` (Postgres) and `web` (Django dev server).

## Installation

Requires [Docker](https://www.docker.com/) with Docker Compose.

1. Clone the repository and enter it:
   ```bash
   git clone <repo-url>
   cd Task_manager
   ```
2. Build and start the containers — no configuration needed, the repo already includes a working `.env`:
   ```bash
   docker compose up -d --build
   ```
   This automatically runs database migrations on startup. On a **fresh, empty database**, one of those migrations also seeds two demo accounts with sample tasks, so there's something to look at immediately:

   | Username | Password | Role |
   |---|---|---|
   | `jblake` | `Harbor42Kite` | Admin |
   | `mchen` | `Violet9Stream` | Member |

   This seeding only happens once, on an empty database — it never touches or resets real data added afterwards.

3. Open [http://localhost:8000](http://localhost:8000) and sign in with one of the accounts above (or your own, once created via the admin's **Add person** button).

### If step 2 fails with `CERTIFICATE_VERIFY_FAILED`

That means something on your machine (a corporate proxy or antivirus with HTTPS inspection) is intercepting the connection `pip` makes to PyPI while building the image — `pip` doesn't trust that interception certificate, even if the rest of your system does. This isn't something fixable inside the image.

The fix that doesn't require you to touch any certificates: load the pre-built image you were given instead of building it locally, then start the containers **without** `--build`:
```bash
docker load -i taskpanel-web-image.tar.gz
docker compose up -d
```
`docker load` and `docker compose up` don't talk to PyPI at all, so the same interception that breaks `pip` doesn't affect this path.

### Useful commands

```bash
docker compose logs -f web       # follow the app logs
docker compose exec web python manage.py createsuperuser   # create an extra Django admin account
docker compose down              # stop the containers (keeps data)
docker compose down -v           # stop and wipe the database completely
```

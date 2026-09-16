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
2. Add the `.env` file to the project root (get it from whoever shared this repo with you — it's not committed to git on purpose, since it holds real secrets/passwords).
3. Build and start the containers:
   ```bash
   docker compose up -d --build
   ```
   This automatically runs database migrations on startup. On a **fresh, empty database**, one of those migrations also seeds two demo accounts with sample tasks, so there's something to look at immediately:

   | Username | Password | Role |
   |---|---|---|
   | `jblake` | `Harbor42Kite` | Admin |
   | `mchen` | `Violet9Stream` | Member |

   This seeding only happens once, on an empty database — it never touches or resets real data added afterwards.

4. Open [http://localhost:8000](http://localhost:8000) and sign in with one of the accounts above (or your own, once created via the admin's **Add person** button).

### Useful commands

```bash
docker compose logs -f web       # follow the app logs
docker compose exec web python manage.py createsuperuser   # create an extra Django admin account
docker compose down              # stop the containers (keeps data)
docker compose down -v           # stop and wipe the database completely
```

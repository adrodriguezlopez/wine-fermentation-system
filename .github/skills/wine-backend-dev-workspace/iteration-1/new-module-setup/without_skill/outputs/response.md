# Setting Up a New `notifications` Module in a FastAPI Project

Before writing any code for a new `notifications` module, here is the recommended setup process:

## 1. Understand the Project Structure

Familiarize yourself with how the existing project is organized and identify which pattern it uses so your `notifications` module fits in consistently.

## 2. Define the Module's Scope and Responsibilities

Before creating files, clarify:
- What triggers a notification?
- What channels will be used? (email, SMS, webhook, push, in-app)
- Who receives notifications?
- Is it synchronous or asynchronous?
- Does it store notification history?

## 3. Identify and Install Dependencies

| Channel | Common Library |
|---|---|
| Email (SMTP) | `smtplib` (stdlib) or `fastapi-mail` |
| SMS | `twilio` |
| Async | `celery`, `redis`, `arq` |

## 4. Create the Module Directory Structure

```
app/
└── notifications/
    ├── __init__.py
    ├── router.py
    ├── service.py
    ├── schemas.py
    ├── models.py
    └── dependencies.py
```

## 5. Set Up Configuration

Add keys to your settings and store secrets in `.env`.

## 6. Plan Database Migrations

If persisting notification history, create a SQLAlchemy model and run Alembic:
```bash
alembic revision --autogenerate -m "add notifications table"
alembic upgrade head
```

## 7. Decide on Background Task Strategy

| Option | Best For |
|---|---|
| FastAPI `BackgroundTasks` | Simple, low-volume |
| Celery + Redis | Reliable, high-volume |

## 8. Plan Router Registration

```python
from app.notifications.router import router as notifications_router
app.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
```

## 9. Create a Test File First

Confirm `pytest`, `httpx`, and `pytest-asyncio` are installed.

## 10. Review Existing Modules for Patterns

Look at an existing module (e.g., `fermentation`) before coding.

## Summary Checklist

- [ ] Reviewed project structure and existing patterns
- [ ] Defined scope: triggers, channels, recipients, sync vs async
- [ ] Installed required libraries
- [ ] Created module scaffolding
- [ ] Added config keys to settings
- [ ] Planned Alembic migration (if history needed)
- [ ] Planned router registration
- [ ] Created empty test file

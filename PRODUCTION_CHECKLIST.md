# Production Checklist

## Environment
- Set `DEBUG=False`
- Set `SECRET_KEY` to a new random value
- Set `ALLOWED_HOSTS` to your domain(s)
- Set `CSRF_TRUSTED_ORIGINS` to your HTTPS domain(s)

## Email
- Set `USE_SMTP_EMAIL=True`
- Configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- Test sending one real email before go-live

## Security
- Enable HTTPS behind a reverse proxy
- Keep `SESSION_COOKIE_SECURE=True`
- Keep `CSRF_COOKIE_SECURE=True`
- Verify `SECURE_SSL_REDIRECT=True`

## Database
- Run `python manage.py migrate`
- Create a production superuser
- Back up the SQLite database or switch to PostgreSQL for production

## Static Files
- Run `python manage.py collectstatic`
- Serve static files from a proper web server

## Smoke Tests
- Login works
- Dashboard loads
- Create invoice works
- Send invoice email works
- Notifications list loads
- Mark as read and dismiss work
- Admin login works

@echo off
REM ============================================================================
REM SCRIPT DE CONFIGURATION EMAIL - Windows PowerShell
REM ============================================================================
REM Ce script configure les variables d'environnement pour l'email SMTP
REM
REM Usage: 
REM   1. Pour GMAIL:
REM      set-email-gmail.bat votre-email@gmail.com "votre-app-password"
REM
REM   2. Pour OUTLOOK:
REM      set-email-outlook.bat votre-email@outlook.com "votre-password"
REM
REM ============================================================================

REM Configuration GMAIL
if "%~1"=="gmail" (
    echo Configuration GMAIL...
    set USE_SMTP_EMAIL=True
    set EMAIL_HOST=smtp.gmail.com
    set EMAIL_PORT=587
    set EMAIL_USE_TLS=True
    set EMAIL_HOST_USER=%~2
    set EMAIL_HOST_PASSWORD=%~3
    set DEFAULT_FROM_EMAIL=noreply@facturation.com
    echo ✓ Variables GMAIL configurées
    echo Execute maintenant:
    echo   venv\Scripts\python.exe manage.py runserver
    goto:eof
)

REM Configuration OUTLOOK
if "%~1"=="outlook" (
    echo Configuration OUTLOOK...
    set USE_SMTP_EMAIL=True
    set EMAIL_HOST=smtp-mail.outlook.com
    set EMAIL_PORT=587
    set EMAIL_USE_TLS=True
    set EMAIL_HOST_USER=%~2
    set EMAIL_HOST_PASSWORD=%~3
    set DEFAULT_FROM_EMAIL=noreply@facturation.com
    echo ✓ Variables OUTLOOK configurées
    echo Execute maintenant:
    echo   venv\Scripts\python.exe manage.py runserver
    goto:eof
)

REM Configuration OVH
if "%~1"=="ovh" (
    echo Configuration OVH...
    set USE_SMTP_EMAIL=True
    set EMAIL_HOST=mail.ovh.net
    set EMAIL_PORT=587
    set EMAIL_USE_TLS=True
    set EMAIL_HOST_USER=%~2
    set EMAIL_HOST_PASSWORD=%~3
    set DEFAULT_FROM_EMAIL=noreply@facturation.com
    echo ✓ Variables OVH configurées
    echo Execute maintenant:
    echo   venv\Scripts\python.exe manage.py runserver
    goto:eof
)

echo Usage:
echo   set-email.bat gmail "email@gmail.com" "app-password"
echo   set-email.bat outlook "email@outlook.com" "password"
echo   set-email.bat ovh "email@domain.fr" "password"

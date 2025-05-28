@echo off
set ROOT=%~dp0..\..
set PYTHON=%ROOT%\.venv\Scripts\python.exe
set ODOO=%ROOT%\src\odoo\odoo-bin

:: Wipe old log file before launching
del %ROOT%\odoo.log >nul 2>&1

%PYTHON% %ODOO% -c %ROOT%\odoo.cfg %*
exit /b %ERRORLEVEL%

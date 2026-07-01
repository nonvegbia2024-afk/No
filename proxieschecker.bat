@echo off
for /F "tokens=*" %%P in (proxies.txt) do (
    echo Testing %%P...
    curl -x http://%%P http://httpbin.org/ip --max-time 8 --silent
    echo.
)
pause
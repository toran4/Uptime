FROM python:3.10-slim-bullseye
COPY *.py sites.txt /Uptime

ENTRYPOINT ["python3", "/Uptime/monitor.py"]
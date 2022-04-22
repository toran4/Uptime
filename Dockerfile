FROM python:3.10-slim-bullseye
RUN pip install requests

COPY *.py sites.txt /Uptime/

WORKDIR /Uptime
ENTRYPOINT ["python3", "/Uptime/monitor.py"]

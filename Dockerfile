FROM python:3.12-alpine

COPY *.sh *.py *.txt /script/

RUN pip install --no-cache-dir -r /script/requirements.txt \
    && chmod +x /script/*.sh \
    && chmod +x /script/*.py \
    && rm -rf /tmp/* /var/tmp/* /var/cache/apk/* /var/cache/distfiles/*

WORKDIR /script
CMD ["sh", "-c", "/script/setup_cron.sh && crond -f"]
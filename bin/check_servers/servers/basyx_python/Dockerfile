FROM tiangolo/uwsgi-nginx:python3.11

# Should match client_body_buffer_size defined in nginx/body-buffer-size.conf
ENV NGINX_MAX_UPLOAD 1M

# object stores aren't thread-safe yet
# https://github.com/eclipse-basyx/basyx-python-sdk/issues/205
ENV UWSGI_CHEAPER 0
ENV UWSGI_PROCESSES 1

COPY app/requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app
COPY ./nginx /etc/nginx/conf.d

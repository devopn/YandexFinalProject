FROM python:3.12.1-alpine3.19

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV POSTGRES_CONN=XXX
ENV SERVER_ADDRESS=XXX
ENV RANDOM_SECRET=XXX

CMD [ "python3", "app.py" ]
# CMD ["sh", "-c", "exec python3 -m flask run --host=0.0.0.0 --port=$SERVER_PORT"] 
# CMD ["gunicorn", "-c", "python:gunicorn_conf", "wsgi:app" ]

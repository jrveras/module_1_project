FROM python:3.8
LABEL maintainer="Jairton Junior"

COPY . /app
WORKDIR /app/techtrends
RUN pip install -r requirements.txt

RUN ["python", "init_db.py"]

EXPOSE 3111

CMD [ "python", "app.py" ]

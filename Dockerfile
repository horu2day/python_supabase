FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 환경 변수 설정
ENV FLET_SERVER_PORT=8000
ENV FLET_FORCE_WEB_VIEW=true

CMD ["python", "main.py"]
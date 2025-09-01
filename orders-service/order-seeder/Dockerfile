FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY seed.py . 
 # or COPY . . if you want everything
RUN pip install httpx

CMD ["python","-u", "seed.py"]

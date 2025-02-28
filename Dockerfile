FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    curl

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "src/scripts/funding_streamlit_app_stable.py", "--server.port=8501", "--server.address=0.0.0.0"] 
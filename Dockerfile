FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV NOVACART_DATABASE=/lab/data/lab.db
WORKDIR /lab
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home labuser
COPY --chown=labuser:labuser . .
RUN mkdir -p /lab/data && chown labuser:labuser /lab/data
USER labuser
EXPOSE 5000
CMD ["python", "app.py", "--container"]

FROM python:3.12-slim
RUN groupadd -r appgroup && useradd -r -u 1000 -g appgroup -d /opt/gdpro user
WORKDIR /opt/gdpro
COPY --chown=user:appgroup . .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt \
    && python manage.py migrate
USER user
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

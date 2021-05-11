FROM python:latest
RUN pip install hvac kubernetes
COPY op.py /op.py
ENTRYPOINT [ "python", "/op.py" ]
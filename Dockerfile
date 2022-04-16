FROM python:3.7.13-alpine3.14
RUN pip install hvac kubernetes kopf
COPY op.py /op.py
ENTRYPOINT [ "kopf", "run", "-A", "/op.py" ]

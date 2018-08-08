FROM ubuntu

RUN mkdir /code
ADD . /code

RUN apt update && \
    apt install -y python3 python3-pip && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install requests python-dateutil pandas flask pyopenssl

CMD python3 /code/app.py

# Version 1.0
FROM python:2.7.15

# 维护者
LABEL maintainer="chenluqq@gmail.com"

ADD requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY ./*.py /app/
COPY ./*.yaml /app/
COPY ./*.jpg /app/

EXPOSE 8888

#指令配置工作目录
WORKDIR /app/

#ENTRYPOINT 运行以下命令
CMD ["python","/app/WeixinServer.py"]


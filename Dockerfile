# 选择编译镜像
FROM python:3.7

WORKDIR /www
COPY requirements.txt .

RUN pip install -i https://pypi.doubanio.com/simple/ -r requirements.txt

# 修改时区
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

WORKDIR /www/explorer_s_common
COPY . /www/explorer_s_common/
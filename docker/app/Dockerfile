FROM python:3.7-slim-buster

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  && apt-get install -y python-dev \
  && apt-get install -y wget \
  && apt-get install -y zip unzip

WORKDIR /usr/src/app

COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

# Install PhantomJs and Casperjs for Testing
ENV PHANTOM_JS="phantomjs-1.9.8-linux-x86_64"
RUN apt-get install -y chrpath libssl-dev libxft-dev \
    && apt-get install -y libfreetype6 libfreetype6-dev \
    && apt-get install -y libfontconfig1 libfontconfig1-dev \
    && apt-get install -y git

RUN cd ../ && wget https://bitbucket.org/ariya/phantomjs/downloads/$PHANTOM_JS.tar.bz2
RUN mv ../$PHANTOM_JS.tar.bz2 /usr/local/share/
RUN cd /usr/local/share/ && tar xvjf $PHANTOM_JS.tar.bz2
RUN ln -sf /usr/local/share/$PHANTOM_JS/bin/phantomjs /usr/local/share/phantomjs
RUN ln -sf /usr/local/share/$PHANTOM_JS/bin/phantomjs /usr/local/bin/phantomjs
RUN ln -sf /usr/local/share/$PHANTOM_JS/bin/phantomjs /usr/bin/phantomjs
RUN rm -rf /usr/local/share/$PHANTOM_JS.tar.bz2

RUN cd ../ && git clone git://github.com/casperjs/casperjs.git \
    && cd casperjs && ln -sf `pwd`/bin/casperjs /usr/local/bin/casperjs

ENV PYTHONPATH="/usr/src/app"
ENV PYTHONUNBUFFERED=1
COPY . .

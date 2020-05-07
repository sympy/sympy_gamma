FROM python:2-slim

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  && apt-get install -y python-dev \
  && apt-get install -y wget \
  && apt-get install -y zip unzip

WORKDIR /usr/src/app

COPY requirements ./requirements
COPY ./docker/app/run.sh /run.sh

RUN pip install -r requirements/requirements.txt -t lib/
RUN pip install -r requirements/local_requirements.txt

# Install App engine SDK
RUN wget https://storage.googleapis.com/appengine-sdks/featured/google_appengine_1.9.90.zip -nv -P /usr/src/
RUN unzip -q /usr/src/google_appengine_1.9.90.zip -d /usr/src/
ENV SDK_LOCATION="/usr/src/google_appengine"

# Install PhantomJs and Casperjs for Testing
ENV PHANTOM_JS="phantomjs-2.1.1-linux-x86_64"
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

COPY . .

ENTRYPOINT [ "/run.sh" ]

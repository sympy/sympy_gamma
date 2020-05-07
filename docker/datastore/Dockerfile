FROM google/cloud-sdk:latest

WORKDIR /usr/src/app
COPY ./docker/datastore/run.sh ./run.sh

ENV CLOUDSDK_CORE_PROJECT=sympy-live-hrd

ENTRYPOINT [ "./run.sh" ]

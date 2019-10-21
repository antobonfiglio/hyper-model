FROM growingdata/hypermodel:xgboost-1.3.74


RUN apk --no-cache add \
    libffi-dev openssl-dev python-dev py-pip build-base

# Hyper model requirements
RUN pip install \
    click \
    kfp \
    pandas \
    google-cloud \
    google-cloud-bigquery \
    tqdm

# For "crashed"
RUN pip install \
    python-gitlab \
    xgboost \
    sklearn 

ADD ./src/hyper-model /crashed/hyper-model
ADD ./demo/car-crashes /crashed/car-crashes


# Install the current source code version of HyperModel
WORKDIR /crashed/hyper-model
RUN pwd
RUN pip install -e .

# Install our actual demo
WORKDIR /crashed/car-crashes
RUN pip install -e .


WORKDIR /crashed
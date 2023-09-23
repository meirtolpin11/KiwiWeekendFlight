FROM ubuntu:22.10

<<<<<<< Updated upstream
RUN apt update 
=======
RUN apt clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt update
>>>>>>> Stashed changes
RUN apt-get install -y libappindicator1 fonts-liberation wget python3 python3-pip
RUN apt-get install -f 

WORKDIR /tmp

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt install -y ./google-chrome-stable_current_amd64.deb

RUN mkdir -p /src

WORKDIR /src

COPY . . 

RUN python3 -m pip install pip IPython -U 
RUN python3 -m pip install -r requirements.txt

ENTRYPOINT python3 main.py --publish


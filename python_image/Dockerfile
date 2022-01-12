FROM ubuntu:18.04
SHELL ["/bin/bash", "-c"]
RUN apt update
RUN apt upgrade -y
RUN apt autoremove
RUN apt autoclean
RUN apt install wget -y
RUN wget -c https://repo.anaconda.com/miniconda/Miniconda3-py37_4.10.3-Linux-x86_64.sh
RUN chmod +x Miniconda3-py37_4.10.3-Linux-x86_64.sh
RUN ./Miniconda3-py37_4.10.3-Linux-x86_64.sh -y -b -p /home/conda
RUN rm -rf Miniconda3-py37_4.10.3-Linux-x86_64.sh
WORKDIR /app/backend
COPY . .
RUN /home/conda/bin/conda init bash
RUN /home/conda/bin/pip config set global.cache-dir false
RUN /home/conda/bin/pip install -r requirements.txt --no-cache-dir
RUN /home/conda/bin/conda install -c conda-forge --file requirements_conda.txt
RUN /home/conda/bin/conda clean -y -a
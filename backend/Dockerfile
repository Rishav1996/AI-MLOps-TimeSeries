FROM python:3.8-slim-buster
RUN /usr/local/bin/python -m pip install --upgrade pip
WORKDIR /app/backend
COPY . .
# RUN /home/conda/bin/conda init bash
# RUN pip config set global.cache-dir false
# RUN /home/conda/bin/conda install -c conda-forge --file requirements_conda.txt
RUN pip install poetry
RUN poetry config installer.max-workers 10
RUN cat requirements.txt | xargs poetry add
# RUN /home/conda/bin/conda clean -y -a
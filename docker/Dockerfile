# Base image
FROM python:3.11
LABEL maintainer=Apollo-Chatchat
WORKDIR /root

# Environment variables
ENV CHATCHAT_ROOT=/root/chatchat_data

# Initialize environment
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime && \
    echo "UTC" > /etc/timezone
RUN apt-get update -y && \
    apt-get install -y git && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip setuptools
RUN pip install --index-url https://pypi.python.org/simple/ pipx && \
    pipx install poetry --force

# Add poetry to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Clone Apollo-Chatchat
RUN git clone https://github.com/Joseff531/Apollo-Chatchat.git

# Install dependencies
WORKDIR /root/Apollo-Chatchat/libs/apollo-chatchat-server
RUN poetry config virtualenvs.create false
RUN poetry install --with lint,test -E xinference

## Make sure Python can find the chatchat module
ENV PYTHONPATH="/root/Apollo-Chatchat/libs/apollo-chatchat-server:${PYTHONPATH}"

# Initialize configuration
WORKDIR /root/Apollo-Chatchat/libs/apollo-chatchat-server/chatchat
RUN python cli.py init

# Initialize knowledge base files
ADD data.tar.gz $CHATCHAT_ROOT/

EXPOSE 7861 8501
ENTRYPOINT ["python", "cli.py", "start", "-a"]

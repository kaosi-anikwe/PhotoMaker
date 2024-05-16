# Use Python 3.8 base image
FROM python:3.8

# Set working directory in the container
WORKDIR /src

# Copy the current directory contents into the container at /app
COPY . /src

# Install required packages
RUN pip install diffusers
RUN pip install accelerate
RUN pip install pip install git+https://github.com/TencentARC/PhotoMaker.git
RUN pip install transformers==4.36.2
RUN pip install torchvision==0.15.2
RUN pip install firebase-admin
RUN pip install -r requirements.txt

# Command to run the Python script
CMD python -u runpod_handler.py

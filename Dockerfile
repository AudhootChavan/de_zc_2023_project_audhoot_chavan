FROM python:3.9 

#Set working directory
WORKDIR /app

#Set entry point as bash
ENTRYPOINT [ "bash" ]

#Copy codes folder
COPY codes codes/

#Install all required python libraries
RUN pip install -r /app/codes/requirements.txt

# Install and update os tools
RUN apt update
RUN apt-get install sudo
RUN apt-get update && apt-get install -y lsb-release && apt-get clean all
RUN apt-get install apt-utils








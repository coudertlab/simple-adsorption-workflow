# Use a Python 3.9 base image
FROM python:3.9.16

# set a directory for the app
WORKDIR /usr/src/app

# copy all the files to the container
COPY . .

# install dependencies from pip
RUN pip install --no-cache-dir -r requirements.txt

# Download and unpack Zeo++ package
RUN wget http://www.zeoplusplus.org/zeo++-0.3.tar.gz
RUN gunzip zeo++-0.3.tar.gz
RUN tar xvf zeo++-0.3.tar

# Compile Voro++ library
WORKDIR /usr/src/app/zeo++-0.3/voro++/src
RUN make

# Compile Zeo++ code
WORKDIR /usr/src/app/zeo++-0.3
RUN make

# Set environment variables
ENV RASPA_PARENT_DIR /usr/local/lib/python3.9/site-packages/RASPA2
ENV RASPA_DIR $RASPA_DIR/gcmc
ENV DYLD_LIBRARY_PATH $RASPA_DIR/lib
ENV LD_LIBRARY_PATH $RASPA_DIR/lib
ENV ZEO_DIR /usr/src/app/zeo++-0.3

# define the port number the container should expose
EXPOSE 5000

# root directory
WORKDIR /usr/src/app

# run the test command
CMD ["python", "./example_adsorption_workflow.py", "-t"]
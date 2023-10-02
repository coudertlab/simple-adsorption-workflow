FROM python:3.9.16

# set a directory for the app
WORKDIR /usr/src/app

# copy all the files to the container
COPY . .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables based on installed package locations
ENV RASPA_PARENT_DIR /usr/local/lib/python3.9/site-packages/RASPA2
ENV RASPA_DIR $RASPA_PARENT_DIR/simulations
ENV DYLD_LIBRARY_PATH $RASPA_DIR/lib
ENV LD_LIBRARY_PATH $RASPA_DIR/lib
ENV ZEO_DIR /usr/local/lib/python3.9/site-packages/zeo++-0.3

# define the port number the container should expose
EXPOSE 5000

# run the test command
CMD ["python", "./example_adsorption_workflow.py", "-t"]

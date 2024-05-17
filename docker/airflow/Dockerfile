FROM apache/airflow:2.9.1

USER airflow

# Install great_expectations and other dependencies
RUN pip install great_expectations asyncpg

# Set environment variables for paths
ENV RAW_DATA_PATH=/opt/airflow/raw-data
ENV GOOD_DATA_PATH=/opt/airflow/good-data
ENV BAD_DATA_PATH=/opt/airflow/bad-data
ENV GE_DIRECTORY=/opt/airflow/gx

# Create necessary directories
RUN mkdir -p $RAW_DATA_PATH $GOOD_DATA_PATH $BAD_DATA_PATH $GE_DIRECTORY

# Copy the Great Expectations configuration directory into the container
COPY great_expectations/ $GE_DIRECTORY/

# Copy your DAGs and other scripts into the container
COPY dags/ /opt/airflow/dags/

# Ensure the copied files have the correct permissions
RUN chown -R airflow:airflow $RAW_DATA_PATH $GOOD_DATA_PATH $BAD_DATA_PATH $GE_DIRECTORY /opt/airflow/dags

# Set the working directory
WORKDIR /opt/airflow

# Expose port 8080
EXPOSE 8080

# Define the default command
CMD ["airflow", "webserver"]

FROM apache/airflow:2.1.0

USER root

# Install great_expectations
RUN pip install great_expectations

# Downgrade typing-extensions to a compatible version
RUN pip install typing-extensions==3.10.0.2

# Upgrade rich to the latest version
RUN pip install rich --upgrade

USER airflow


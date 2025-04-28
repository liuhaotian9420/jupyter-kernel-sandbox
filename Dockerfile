# Dockerfile
FROM jupyter/base-notebook:python-3.10
RUN pip install ipykernel requests fastapi uvicorn websocket-client
USER root

# Copy in your custom kernel spec
COPY kernels/sandbox-python \
     /home/jovyan/.local/share/jupyter/kernels/sandbox-python

# Fix ownership so jovyan can write to runtime dirs
RUN chown -R jovyan:users \
       /home/jovyan/.local/share/jupyter

USER jovyan

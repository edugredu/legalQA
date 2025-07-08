.PHONY: build run attach logs stop rm rebuild shell jupyter

# Modify these names if you change the repo / image name
IMAGE ?= legalqa
CONTAINER ?= legalqa
TAG ?= latest

# Build the Docker image
build:
	docker build -t $(IMAGE):$(TAG) .

# Run container in interactive mode, mount current directory, expose Jupyter port
run:
	docker run -it --name $(CONTAINER) -p 8888:8888 -v $(PWD):/app $(IMAGE):$(TAG) bash

# Launch Jupyter Lab inside the container for a visual interface
jupyter:
	docker run -it --name $(CONTAINER) -p 8888:8888 -v $(PWD):/app $(IMAGE):$(TAG) jupyter lab --ip=0.0.0.0 --no-browser --allow-root --NotebookApp.token=''

# Start a temporary shell without creating a named container
shell:
	docker run --rm -it -v $(PWD):/app $(IMAGE):$(TAG) bash

# Attach to a running container's shell
attach:
	docker exec -it $(CONTAINER) bash

# View container logs
logs:
	docker logs -f $(CONTAINER)

# Stop the running container
stop:
	docker stop $(CONTAINER)

# Remove the stopped container
rm:
	docker rm $(CONTAINER)

# Stop & remove container, then rebuild image and run
rebuild: stop rm build run

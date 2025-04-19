# RAGPipes

RAGPipes is a container based MQTT driven RAG (Retrieval-Augmented Generation) pipeline framework. Consisting of several primitive node types (e.g. `Loader`, `Chunker`, `VectorStore`) each run as an individual container with its own configuration, provided using environment variables. The nodes are connected using MQTT topics, also specified using environment variables.

## Features

- **Modular**: Each node is a separate container, making it easy to scale and manage.
- **MQTT Driven**: Nodes communicate using MQTT topics, making it easy to integrate with other systems.
- **Configurable**: Each node is configured using environment variables, making it easy to deploy and manage.
- **Extensible**: New node types can be easily added by creating new containers.

It is designed to be used with [MQTT](https://mqtt.org/) and [LangChain](https://www.langchain.com/).

## Quick Start

To get started with RAGPipes, check out the example provided [`docker-compose.yml`](./docker-compose.yml) file. This file contains a simple pipeline that has multiple loaders, chunkers and vector store configurations.

    docker-compose up -d

You can inspect what is happening by subscribing to the root MQTT topic:

    mosquitto_sub -h localhost -t "ragpipes/#"

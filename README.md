# RAGPipes

[![docker](https://github.com/jinglemansweep/ragpipes/actions/workflows/docker.yml/badge.svg)](https://github.com/jinglemansweep/ragpipes/actions/workflows/docker.yml)
[![mypy](https://github.com/jinglemansweep/ragpipes/actions/workflows/mypy.yml/badge.svg)](https://github.com/jinglemansweep/ragpipes/actions/workflows/mypy.yml) [![flake8](https://github.com/jinglemansweep/ragpipes/actions/workflows/flake8.yml/badge.svg)](https://github.com/jinglemansweep/ragpipes/actions/workflows/flake8.yml) [![black](https://github.com/jinglemansweep/ragpipes/actions/workflows/black.yml/badge.svg)](https://github.com/jinglemansweep/ragpipes/actions/workflows/black.yml) [![codeql](https://github.com/jinglemansweep/ragpipes/actions/workflows/codeql.yml/badge.svg)](https://github.com/jinglemansweep/ragpipes/actions/workflows/codeql.yml) [![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

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

## Concepts

### Nodes

Nodes are the building blocks of RAGPipes. Each node is a separate container that listens to one or more MQTT topics and publishes to one or more topics. The type of node that runs is controlled using the `RAGPIPES_MQTT__HANDLER` environment variable, for example, set to `chunker` or `loader-web` to run the chunker or web loader nodes respectively.

### Messages

Each node must comply with a standard MQTT JSON payload format. This means each node can be used interchangeably with any other node that complies with the same format. The message format is as follows:

    {
        "docs": List<Document> = []
        "options": Dict[str, Any] = {}
        "outputs": Dict[str, Any] = {}
        "metadata": Dict[str, Any] = {}
    }

`Document` is a [LangChain document](https://python.langchain.com/v0.2/docs/concepts/#document), which is a dictionary with `page_content` and `metadata` properties.

As an example, a chunker node might receive a message with a list of documents (in `docs` property). It will chunk them into smaller parts and then output the resulting chunked documents (in `docs` property).

Options (or variables) can be passed to nodes using the `options` property. For example, a chunker node can be configured to chunk documents into a specific size by setting the `chunk_size` option.

Outputs can be used to pass extra/miscellaneous data between nodes, or to provide status information. For example, a loader node can output the number of documents processed in the `outputs` property.

**TODO: Metadata is not used correctly or defined yet!**

### Pipelines

Pipelines are defined using a [`docker-compose.yml`](./docker-compose.yml) file, or with any other container orchestration tool. Each pipeline consists of multiple nodes (or services/containers), that are can communicate with each other using MQTT topics.

Each node will subscribe (or listen to) one or more MQTT topics. This is achieved by setting the `RAGPIPES_MQTT__TOPIC_COMMAND` environment variable to either a single topic (e.g. `ragpipes/loaders/web/command`) or a list of topics separated by commas (e.g. `ragpipes/loaders/web/command,ragpipes/loaders/text/command`). Nodes will respond by publishing its output to one or more MQTT topics. This is achieved by setting the `RAGPIPES_MQTT__TOPIC_RESPONSE` environment variable to either a single topic, or a comma separated list of topics.

For example:

- **Web Loader** nodes subscribe to `ragpipes/loaders/web/command` and publishes output to a Chunker nodes command topic (e.g. `ragpipes/chunker/default/command`). Upon message receipt, the web sloader with fetch the webpage using the provided `url` parameter, and publish the page content to its response topics.
- **Chunker** nodes subscribe to `ragpipes/loaders/web/command` and publishes output to a **Vectore Store** nodes command topic (e.g. `ragpipes/vectorstore/default/command`). Upon message receipt, the chunker will chunk/split the provided content into smaller chunks, and publish the content to its response topics.
- **Vector Store** nodes subscribe to `ragpipes/vectorstore/default/command`. Upon message receipt, the vectore store node will persist the provided documents into its configured vector store database.
- **Chat** nodes subscribe to `ragpipes/chat/default/command` and have a direct connection to the vector store database. Upon message receipt, the chat node will retrieve the documents from the vector store, generate a response, and then publish the response to the `ragpipes/chat/default/response` topic.

### Deployment

Docker Compose Example:

Create a `.env` file using the provided example [`.env.example`](./.env.example) file and set the required environment variables. Use the provided [docker-compose.yml](./docker-compose.yml) file to deploy the services:

    docker compose up -d

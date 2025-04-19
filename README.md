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

### Pipelines

The pipelines are defined in the `docker-compose.yml` file. Each pipeline node is a separate service that listens to a specific MQTT topic and publishes to another topic. This is achieved by setting the `RAGPIPES_MQTT__HANDLER` environment variable to the name of the node type and the `RAGPIPES_MQTT__TOPIC_COMMAND` and `RAGPIPES_MQTT__TOPIC_RESPONSE` environment variables to the MQTT topics to listen to and publish to.

For example:

- The **web loader** node can listen to the `ragpipes/loaders/web/command` topic. Once a message is received, it will load the web page, chunk it, and publish the page content to the `ragpipes/chunker/default/command` topic.
- The **text loader** node can listen to the `ragpipes/loaders/text/command` topic. Once a message is received, it will also publish the text content to the `ragpipes/chunker/default/command` topic.
- The **chunker** node can listen to the `ragpipes/chunker/default/command` topic, for messages from both the web loader and text loader nodes. Once a message is received, it will chunk the content according to its configuration and publish to the `ragpipes/chunker/default/response` topic.
- The **vector store** node can listen to the `ragpipes/chunker/default/response` topic. On receiving a message, it will persist the chunked response in the underlying vector store engine and then publishes the status to the `ragpipes/vectorstore/default/response` topic.
- The **chat** node can listen to the `ragpipes/chat/default/command` topic. When a message is received, it will retrieve the documents from the vector store, generate a response, and then publish the response to the `ragpipes/chat/default/response` topic. Each chat node must be configured with the vector store configuration it should use to retrieve the documents.

Docker Compose Example:

Create a `.env` file using the provided example [`.env.example`](./.env.example) file and set the required environment variables, and then create a Docker Compose file as follows:

    services:

      loader-web:
        build:
          context: .
          dockerfile: Dockerfile
          env_file:
            - .env
        environment:
         - RAGPIPES_MQTT__HANDLER=loader.web
         - RAGPIPES_MQTT__TOPIC_COMMAND=ragpipes/loader/web/command
         - RAGPIPES_MQTT__TOPIC_RESPONSE=ragpipes/chunker/default/command

     chunker-default:
        build:
          context: .
          dockerfile: Dockerfile
          env_file:
            - .env
        environment:
         - RAGPIPES_MQTT__HANDLER=chunker
         - RAGPIPES_MQTT__TOPIC_COMMAND=ragpipes/chunker/default/command
         - RAGPIPES_MQTT__TOPIC_RESPONSE=ragpipes/chunker/default/response

    vectorstore-default:
        build:
          context: .
          dockerfile: Dockerfile
          env_file:
            - .env
        environment:
         - RAGPIPES_MQTT__HANDLER=vectorstore
         - RAGPIPES_MQTT__TOPIC_COMMAND=ragpipes/chunker/default/response
         - RAGPIPES_MQTT__TOPIC_RESPONSE=ragpipes/vectorstore/default/response
         - RAGPIPES_PGVECTOR__COLLECTION=my_collection

    chat-default:
       build:
          context: .
          dockerfile: Dockerfile
          env_file:
            - .env
        environment:
         - RAGPIPES_MQTT__HANDLER=chat
         - RAGPIPES_MQTT__TOPIC_COMMAND=ragpipes/chat/default/command
         - RAGPIPES_MQTT__TOPIC_RESPONSE=ragpipes/chat/default/response
         - RAGPIPES_PGVECTOR__COLLECTION=my_collection

### MQTT Examples

    mosquitto_pub -h localhost -t "<TOPIC>" -m '{"data": <COMMAND>, "metadata": <METADATA>}'

For example:

    mosquitto_pub -h localhost \
      -t "ragpipes/loaders/web/command" \
      -m '{"data":{"url":"https://www.example.com"},"metadata":{"author":"John Doe"}}'

#### Loader: Web (`ragpipes/loaders/web/command`)

Command:

    { "url": "https://www.example.com" }

Response:

    { "docs": [Document, ...] }

#### Loader: Wikipedia (`ragpipes/loaders/wikipedia/command`)

Command:

    { "query": "World Cup" }

Response:

    { "docs": [Document, ...] }

#### Chunker

Command:

    { "docs": [Document, ...] }

Response:

    { "docs": [Document, ...] }

#### VectorStore: PGVector (`ragpipes/vectorstores/pgvector/command`)

Command:

    { "docs": [Document, ...] }

Response:

    { "added": 10, "collection": "default" }

#### Chat (`ragpipes/chat/default/command`)

Command:

    { "query": "What is the capital of France?" }

Response:

    {
      "answer": "The capital of France is Paris.",
      "context": [Document, ...],
    }

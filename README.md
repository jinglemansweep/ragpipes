# RAGPipes

[![docker](https://github.com/jinglemansweep/ragpipes/actions/workflows/docker.yml/badge.svg)](https://github.com/jinglemansweep/ragpipes/actions/workflows/docker.yml)
[![mypy](https://github.com/jinglemansweep/ragpipes/actions/workflows/mypy.yml/badge.svg)](https://github.com/jinglemansweep/ragpipes/actions/workflows/mypy.yml) [![flake8](https://github.com/jinglemansweep/ragpipes/actions/workflows/flake8.yml/badge.svg)](https://github.com/jinglemansweep/ragpipes/actions/workflows/flake8.yml) [![black](https://github.com/jinglemansweep/ragpipes/actions/workflows/black.yml/badge.svg)](https://github.com/jinglemansweep/ragpipes/actions/workflows/black.yml) [![codeql](https://github.com/jinglemansweep/ragpipes/actions/workflows/codeql.yml/badge.svg)](https://github.com/jinglemansweep/ragpipes/actions/workflows/codeql.yml) [![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

RAGPipes is a container based MQTT driven RAG (Retrieval-Augmented Generation) pipeline framework. Consisting of several primitive node types (e.g. `Loader`, `Chunker`, `VectorStore`) each run as an individual container with its own configuration, provided using environment variables. The nodes are connected using MQTT topics, also specified using environment variables.

             +--------+     +---------+     +--------+
    MQTT --> | Loader | --> | Chunker | --> | Vector |
             +--------+     +---------+     +--------+
                                                 |
             +--------+                          |
    MQTT --> |  Chat  | <------------------------+
             +--------+

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

### MQTT Examples

    mosquitto_pub -h localhost -t "<TOPIC>" -m "<JSON>"

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

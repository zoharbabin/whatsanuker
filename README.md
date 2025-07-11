# Whatsanuker

Whatsanuker is a plug-and-play, AI-driven gatekeeper for WhatsApp Communities.
It vets join requests, snipes spam, and boots bad actors in real time—running locally with WhatsApp-Web.js and Claude-Sonnet on AWS Bedrock (via LiteLLM).

## Running the dev container

This repository includes a development container configuration for Node.js 20.

1. Install [Docker](https://www.docker.com/) and [Visual Studio Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).
2. Open this project in VS Code.
3. When prompted, choose **Reopen in Container** to build and start the environment using Node 20.

Alternatively, if you have the [devcontainer CLI](https://github.com/devcontainers/cli) installed, run:

```bash
devcontainer up --workspace-folder .
```

# DocAudit

DocAudit is a tool for reviewing documents in the field of information security. When reviewing the documentation of an ISMS (Information Security Management System), it is often necessary to review a large amount of documents. DocAudit supports information security experts in their document work by enabling a semantic search across multiple documents. In this way, passages of text relating to information security measures can be found more quickly than is the case when documents are searched manually.

## Installation

DocAudit consists of two components, the web API and the [web client](https://github.com/hutschen/doc-audit-ng). This repository contains the web API. For installation in a production environment, deployment using Docker is recommended. You can find the appropriate Docker image on [Docker Hub](https://hub.docker.com/r/hutschen/doc-audit) or you can build by using the Dockerfile, which you can find in [a separate repository](https://github.com/hutschen/doc-audit-docker).

## Contributing

The goal of DocAudit is to provide its users with the greatest possible benefit in their daily work in information security. For this reason, feedback from the field and suggestions for improvement are particularly important.

If you want to contribute something like this, feel free to create an issue with a feature request, an idea for improvement or a bug report. Issues can be created in English and German.

This project is just started. Later there will be more possibilities to contribute. For now please be patient. Thanks :relaxed:

## License and dependencies

The DocAudit itself or the source code in this repository is licensed under AGPLv3. You find the license in the [license file](LICENSE). In addition, DocAudit uses a number of libraries to make it work. These libraries have been released by their respective authors under their own licenses. These libraries or their source code is not part of this repository.

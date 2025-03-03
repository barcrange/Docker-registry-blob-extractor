# Docker-registry-blob-extractor

Designed to interact with unauthenticated Docker registry APIs (v2). It allows you to enumerate repositories, list tags, download image layer blobs (tar.gz files), and automatically extract them for further analysis. This tool is useful for security auditing, incident response, and exploring Docker registries.

 usage:
 ```
python docker_registry_explorer.py -u https://<registry-ip>:<port>
```

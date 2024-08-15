# 🐳 Immich Auto Stack - Docker Edition

![](images/stacks.png)

This is a simple Pyhon script, dressed as a Docker container, that stacks together photos. Immich has stacks, yes. They are not editable through the UI.

![](images/strip.png)

⚠️ Currently, it stacks together only **JPG + RAW** files. This behavior can be altered by using a different stacking criteria. If you have ideas, do share them.

The script can be run manually, or via cronjob by providing a crontab expression to the container. The container can be added to the Immich compose stack directly.

### 🔑 Obtaining an Immich API key
Instructions can be found in the Immich docs - [Obtain the API key](https://immich.app/docs/features/command-line-interface#obtain-the-api-key)

### 🔂 Running once
To perform a manually triggered run, use the following command:

```bash
docker run --rm -e API_URL="https://immich.mydomain.com/api/" -e API_KEY="xxxxx" -e SKIP_PREVIOUS=True ghcr.io/tenekev/immich-auto-stack:latest /script/immich_auto_stack.sh
```

### 🔁 Running on a schedule
```bash
docker run --name immich-auto-stack -e TZ="Europe/Sofia" -e CRON_EXPRESSION="0 * * * *" -e API_URL="https://immich.mydomain.com/api/" -e API_KEY="xxxxx" -e SKIP_PREVIOUS=True ghcr.io/tenekev/immich-auto-stack:latest
```

### 📃 Running as part of the Immich docker-compose.yml
Adding the container to Immich's `docker-compose.yml` file:

```yml
version: "3.8"
...
services:
  immich-server:
    container_name: immich_server
  ...

  immich-auto-stack:
    container_name: immich-auto-stack
    image: ghcr.io/tenekev/immich-auto-stack:latest
    restart: unless-stopped
    environment:
      API_URL: http://immich_server:3001/api
      API_KEY: xxxxxxxxxxxxxxxxx               # https://immich.app/docs/features/command-line-interface#obtain-the-api-key
      SKIP_PREVIOUS: True                      # Whether or not to modify photos that are already in stacks. Going over all assets takes a lot more time.
      CRON_EXPRESSION: "0 */1 * * *"           # Run every hour
      TZ: Europe/Sofia
```

You can still trigger the script manually by issuing the following command in the container shell:
```sh
/script/immich_auto_stack.sh
```
Or with Docker exec:
```sh
docker exec -it immich-auto-stack /script/immich_auto_stack.sh
```

## Customizing the criteria

Configurable criteria allows for the customization of how files are grouped
The default is equivalent to:

```python
lambda x: (
  x["originalFileName"].split(".")[0],
  x["localDateTime"]
)
```

To override the default, pass a new configuration file into docker via
The CRITERIA env var.

```shell
docker -e CRITERIA='[{"key": "originalFileName", "split": {"key": "_", "index": 0}}]' ...
``` 

## Parent priority

Keywords can be provided to prioritize the file that is selected as the parent. For example:

```shell
docker -e PARENT_PROMOTE="edit,crop,hdr" ...
``` 

## License

This project is licensed under the GNU Affero General Public License version 3 (AGPLv3) to align with the licensing of Immich, which this script interacts with. For more details on the rights and obligations under this license, see the [GNU licenses page](https://opensource.org/license/agpl-v3).


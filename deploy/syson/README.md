# SysON Local Environment

This is a local test deployment of Eclipse SysON, a graphical open-source SysML v2 editor.

Create a local runtime env file first:

```bash
cp deploy/syson/.env.example deploy/syson/.env
```

Set `SYSON_POSTGRES_PASSWORD` in `deploy/syson/.env` before starting a new
environment. The runtime `.env` file is ignored by git.

Start:

```bash
docker compose -f deploy/syson/docker-compose.yml up -d
```

Open:

```text
http://localhost:18090
```

Stop:

```bash
docker compose -f deploy/syson/docker-compose.yml down
```

The Postgres database is bind-mounted at `deploy/syson/data/postgres` so SysON test projects survive normal container recreation.

Notes:

- SysON is a separate editor/repository stack from the local OpenMBEE Flexo MMS stack.
- SysON documentation currently says the standard SysML v2 REST API is not fully available yet, so direct live editing against Flexo is not expected to work out of the box.
- Use SysML v2 textual/file exchange for interoperability experiments between SysON and Flexo.

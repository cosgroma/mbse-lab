.PHONY: help init up down status logs check eval bridge-eval live-eval secret-scan backup rotate-secrets syson-up syson-down syson-status flexo-list syson-list

help:
	@printf '%s\n' 'MBSE local lab commands:'
	@printf '  %-16s %s\n' 'init' 'Generate Flexo runtime env files and compose setup'
	@printf '  %-16s %s\n' 'up' 'Start Flexo and SysON'
	@printf '  %-16s %s\n' 'down' 'Stop Flexo and SysON'
	@printf '  %-16s %s\n' 'status' 'Check local service status'
	@printf '  %-16s %s\n' 'check' 'Run static validation and secret scan'
	@printf '  %-16s %s\n' 'eval' 'Run deterministic local evals'
	@printf '  %-16s %s\n' 'live-eval' 'Run optional live service evals'
	@printf '  %-16s %s\n' 'backup' 'Export Flexo Fuseki data and refresh startup dataset'
	@printf '  %-16s %s\n' 'rotate-secrets' 'Regenerate ignored local Flexo runtime secrets'
	@printf '  %-16s %s\n' 'flexo-list' 'List Flexo SysML v2 projects'
	@printf '  %-16s %s\n' 'syson-list' 'List SysON projects'

init:
	python3 scripts/flexo_mms_env.py init --with-sysmlv2

up:
	python3 scripts/flexo_mms_env.py up --wait --timeout 60
	docker compose -f deploy/syson/docker-compose.yml up -d

down:
	docker compose -f deploy/syson/docker-compose.yml down
	python3 scripts/flexo_mms_env.py down

status:
	python3 scripts/flexo_mms_env.py status --with-sysmlv2 --strict
	docker compose -f deploy/syson/docker-compose.yml ps

logs:
	python3 scripts/flexo_mms_env.py logs --tail 100
	docker compose -f deploy/syson/docker-compose.yml logs --tail 100 app

check:
	python3 -m py_compile scripts/flexo_mms_env.py scripts/flexo_syson_bridge.py
	docker compose -f deploy/flexo-mms/docker-compose.yml config --quiet
	docker compose -f deploy/syson/docker-compose.yml config --quiet
	$(MAKE) eval
	$(MAKE) secret-scan
	git status --short

eval: bridge-eval

bridge-eval:
	python3 -m unittest discover -s evals -p 'test_bridge_*.py'

live-eval:
	MBSE_LIVE_EVAL=1 python3 -m unittest discover -s evals -p 'test_live_*.py'

secret-scan:
	@git grep -n -E 'thisissomethingreallylon[g]|admi[n]test|adminpasswor[d]|passwor[d]1|passwor[d]2|eyJhb[G]ci|SYSON_POSTGRES_PASSWORD=passwor[d]|JWT_SECRET=thi[s]' HEAD || true

backup:
	python3 scripts/flexo_mms_env.py backup

rotate-secrets:
	python3 scripts/flexo_mms_env.py rotate-secrets

syson-up:
	docker compose -f deploy/syson/docker-compose.yml up -d

syson-down:
	docker compose -f deploy/syson/docker-compose.yml down

syson-status:
	docker compose -f deploy/syson/docker-compose.yml ps

flexo-list:
	python3 scripts/flexo_syson_bridge.py flexo-list-projects

syson-list:
	python3 scripts/flexo_syson_bridge.py syson-list-projects

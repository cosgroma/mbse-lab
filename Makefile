.PHONY: help install-cli bootstrap first-model doctor report cleanup share-check init up down status logs diagnostics check docs-check docs-build docs-serve workflow-check eval bridge-eval live-eval secret-scan backup rotate-secrets syson-up syson-down syson-status flexo-list syson-list deployment-contract deployment-verify

help:
	@printf '%s\n' 'MBSE local lab commands:'
	@printf '  %-16s %s\n' 'init' 'Generate Flexo runtime env files and compose setup'
	@printf '  %-16s %s\n' 'install-cli' 'Install the mbse-lab CLI in editable mode'
	@printf '  %-16s %s\n' 'bootstrap' 'Prepare and start the local SysML v2 lab'
	@printf '  %-16s %s\n' 'first-model' 'Create a tiny Flexo model and import it into SysON'
	@printf '  %-16s %s\n' 'doctor' 'Run mbse-lab environment checks'
	@printf '  %-16s %s\n' 'report' 'Generate reports/latest local lab report'
	@printf '  %-16s %s\n' 'cleanup' 'Remove generated reports, diagnostics, runs, and tmp output'
	@printf '  %-16s %s\n' 'share-check' 'Check for accidental private data before sharing'
	@printf '  %-16s %s\n' 'up' 'Start Flexo and SysON'
	@printf '  %-16s %s\n' 'down' 'Stop Flexo and SysON'
	@printf '  %-16s %s\n' 'status' 'Check local service status'
	@printf '  %-16s %s\n' 'diagnostics' 'Collect diagnostics/latest bundle'
	@printf '  %-16s %s\n' 'check' 'Run static validation and share checks'
	@printf '  %-16s %s\n' 'docs-check' 'Validate docs links and command snippets'
	@printf '  %-16s %s\n' 'docs-build' 'Build the MkDocs documentation site'
	@printf '  %-16s %s\n' 'docs-serve' 'Serve the MkDocs documentation site locally'
	@printf '  %-16s %s\n' 'workflow-check' 'Validate WORKFLOW.md policy contract'
	@printf '  %-16s %s\n' 'eval' 'Run deterministic local evals'
	@printf '  %-16s %s\n' 'live-eval' 'Run optional live service evals'
	@printf '  %-16s %s\n' 'backup' 'Export Flexo Fuseki data and refresh startup dataset'
	@printf '  %-16s %s\n' 'rotate-secrets' 'Regenerate ignored local Flexo runtime secrets'
	@printf '  %-16s %s\n' 'flexo-list' 'List Flexo SysML v2 projects'
	@printf '  %-16s %s\n' 'syson-list' 'List SysON projects'
	@printf '  %-16s %s\n' 'deployment-contract' 'Show fixture-derived deployment runtime contract'
	@printf '  %-16s %s\n' 'deployment-verify' 'Verify Docker runtime against deployment contract'

init:
	python3 scripts/flexo_mms_env.py init --with-sysmlv2

install-cli:
	python3 -m pip install -e .

bootstrap:
	mbse-lab bootstrap

first-model:
	mbse-lab first-model "First Model"

doctor:
	mbse-lab doctor

report:
	mbse-lab report

cleanup:
	mbse-lab cleanup

share-check:
	PYTHONPATH=src python3 -m mbse_lab.cli share-check

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

diagnostics:
	python3 scripts/collect_diagnostics.py

check:
	python3 -m py_compile scripts/flexo_mms_env.py scripts/flexo_syson_bridge.py scripts/collect_diagnostics.py scripts/check_docs.py src/mbse_lab/*.py
	docker compose -f deploy/flexo-mms/docker-compose.yml config --quiet
	docker compose -f deploy/syson/docker-compose.yml config --quiet
	$(MAKE) workflow-check
	$(MAKE) docs-check
	$(MAKE) eval
	$(MAKE) share-check
	git status --short

docs-check:
	python3 scripts/check_docs.py

docs-build:
	hatch run docs:build

docs-serve:
	hatch run docs:serve

workflow-check:
	python3 scripts/check_docs.py --workflow-only

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
	mbse-lab flexo list

syson-list:
	mbse-lab syson list

deployment-contract:
	mbse-lab deployment contract

deployment-verify:
	mbse-lab deployment verify

.phony:
	test

PROJECT_NAME=$(notdir $(PWD))
HOST_NAME=$(USER)
CONTAINER_UID=$(HOSTNAME)_$(PROJECT_NAME)

test-local:
	@echo "*** `tests` directory should exist at project root. Stop."

db-migration:
	alembic -x data=true downgrade base
	alembic -x data=true upgrade head

test-unit:
	pytest --color=yes --showlocals --tb=short -v tests/auth/unit

test-integration:
	pytest --color=yes --showlocals --tb=short -v tests/auth/integration
	
test-e2e:
	pytest --color=yes --showlocals --tb=short -v tests/auth/e2e

test-local: tests db-migration test-unit test-integration test-e2e

build:
	docker-compose build

test:
	docker-compose -p $(CONTAINER_UID) run --rm --use-aliases --service-ports web docker/test.sh

clean:
	docker-compose -p $(CONTAINER_UID) down --remove-orphans --rmi all 2>/dev/null

web:
	docker-compose -p $(CONTAINER_UID) up

prune:
	docker system prune -af



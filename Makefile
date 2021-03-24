.phony:
	test

PROJECT_NAME=$(notdir $(PWD))
HOST_NAME=${USER}
CONTAINER_UID=$(HOST_NAME)_${PROJECT_NAME}
export PROJECT_NAME $(PROJECT_NAME)

# Sanity check & removal of idle postgres images
IDLE_CONTAINERS = $(shell docker ps -aq -f name=postgres -f name=web)
UP_CONTAINERS = $(shell docker ps -q -f name=postgres -f name=web)

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
	@docker-compose build 

test:
	@docker-compose -p $(CONTAINER_UID) run --rm --use-aliases --service-ports web sh docker/test.sh
	@docker kill $(PROJECT_NAME)_postgres
	@docker rm $(PROJECT_NAME)_postgres

clean:
	@docker-compose -p $(CONTAINER_UID) down --remove-orphans  2>/dev/null
	@[ ! -z "$(UP_CONTAINERS)" ] && docker kill $(UP_CONTAINERS) || echo "Neat."
	@[ ! -z "$(IDLE_CONTAINERS)" ] && docker rm $(IDLE_CONTAINERS) || echo "Clean."

service:
	@docker-compose -p $(CONTAINER_UID) up 

prune:
	docker system prune -af



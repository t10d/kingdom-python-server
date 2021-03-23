.phony:
	test

PROJECT_NAME=$(notdir $(PWD))
HOST_NAME=$USER
CONTAINER_UID=$(HOSTNAME)_$PROJECT_NAME

# Sanity check & removal of idle postgres images
IDLE_CONTAINERS = $(shell docker ps -aq -f name=postgres -f name=web)

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
	docker-compose -p $(CONTAINER_UID) run --rm --use-aliases --service-ports web sh docker/test.sh

clean:
	@[ ! -z $(IDLE_CONTAINERS) ] && (docker kill $(IDLE_CONTAINERS) && docker rm $(IDLE_CONTAINERS))
	@docker-compose -p $(CONTAINER_UID) down --remove-orphans  2>/dev/null

web:
	docker-compose -p $(CONTAINER_UID) up 

prune:
	docker system prune -af



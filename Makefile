.phony:
	test


tests:
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

test: tests db-migration test-unit test-integration test-e2e


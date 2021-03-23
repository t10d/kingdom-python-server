#!/bash/sh
sh docker/migration.sh
pytest --color=yes --showlocals --tb=short -v tests/auth/unit
pytest --color=yes --showlocals --tb=short -v tests/auth/integration
pytest --color=yes --showlocals --tb=short -v tests/auth/e2e

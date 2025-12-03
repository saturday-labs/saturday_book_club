PYTHON ?= python3
UV_INSTALL_SCRIPT ?= https://astral.sh/uv/install.sh

.PHONY: init python-version  install-uv install-pre-commit pre-commit-hooks

python-version:
	@$(PYTHON) --version

install-uv:
	@command -v uv >/dev/null 2>&1 || (curl -LsSf $(UV_INSTALL_SCRIPT) | sh)
	@echo "UV installed successfully."

init-uv:
	@uv init
	@uv venv
	@echo "UV environment initialized."

install-pre-commit:
	@uv add pre-commit
	@echo "pre-commit installed successfully."

pre-commit-hooks:
	@GIT_CONFIG_PARAMETERS="'core.hooksPath='" uv run pre-commit install
	@GIT_CONFIG_PARAMETERS="'core.hooksPath='" uv run pre-commit install --hook-type commit-msg
	@echo "pre-commit hooks installed successfully."

init: python-version install-uv init-uv install-pre-commit pre-commit-hooks

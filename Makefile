###############################################################################
# CONFIGURATION                                                               #
###############################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = Dog Breed Model

PYTHON = python
PKG_MGR = pipenv
TENSORBOARD = tensorboard
UNIT_TEST = pytest


###############################################################################
# SETUP                                                                       #
###############################################################################

IPYK_NAME = dog-breed-model
IPYK_DISPLAY_NAME := $(PROJECT_NAME)

SUBDIR_ROOTS := src notebooks scripts tests
DIRS := . $(shell find $(SUBDIR_ROOTS) -type d)
GARBAGE_PATTERNS := *.pyc *~ *-checkpoint.ipynb
GARBAGE := $(foreach DIR,$(DIRS),$(addprefix $(DIR)/,$(GARBAGE_PATTERNS)))

ifeq ($(PKG_MGR), pipenv)
    RUN_PRE = pipenv run
    INSTALL_DEPENDENCIES = pipenv install
    GENERATE_DEPENDENCIES = pipenv lock -r > requirements.txt
    CREATE_VENV =
    REMOVE_VENV = pipenv --rm
else
    RUN_PRE =
    INSTALL_DEPENDENCIES = pip install -r requirements.txt
    GENERATE_DEPENDENCIES = pip freeze --local > requirements.txt
    CREATE_VENV = virtualenv env/
    REMOVE_VENV = rm -rf env/
endif

PYTHON := $(RUN_PRE) $(PYTHON)
TENSORBOARD := $(RUN_PRE) $(TENSORBOARD)
UNIT_TEST := $(RUN_PRE) $(UNIT_TEST)

###############################################################################
# COMMANDS                                                                    #
###############################################################################
.PHONY: help \
        requirements requirements-generate \
        data-get data-process data-cook \
        media-generate \
        environment-create environment-remove environment-test \
        ipykernel-install ipykernel-uninstall \
        clean clean-data clean-media \
		lint

.DEFAULT-GOAL := help

# Misc. helpers

help: ## Displays this help message
	@printf 'Usage: make \033[36m[target]\033[0m\n'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ''

setup: environment-create requirements ipykernel-install ## Creates the project environement.

teardown: ipykernel-uninstall environment-remove ## Removes the project environment.

# Data

data: clean-data data-get data-process data-cook ## Gets and processes the project's data.

data-get: ## Gets the data and stores it locally
	@echo ">>> Getting the data"
	@$(PYTHON) ./scripts/data.py get

data-process: ## Processes the raw data and stores the processed result
	@echo ">>> Processing the data"
	@$(PYTHON) ./scripts/data.py process

data-cook: ## Cooks the processed data and saves the results
	@echo ">>> Cooking the data"
	@$(PYTHON) ./scripts/data.py cook

# Media

media-generate: ## Generates media files for the project
	@echo ">>> Generating media files"
	@$(RUN_PRE) ./scripts/media.py generate

# Tools

tensorboard: ## Starts TensorBoard
	$(TENSORBOARD) --logdir=logs/ 

# Requirements

requirements: ## Installs Python dependencies
	$(INSTALL_DEPENDENCIES)

requirements-generate: ## Generates the project's requirements.txt file
	$(GENERATE_DEPENDENCIES)

# Environment

environment-create: ## Create a new Python virtual environment
	@echo ">>> Creating new virtual environment for project"
	$(CREATE_VENV)

environment-remove: ## Removes the created Python virtual environment
	@echo ">>> Removing the project virtual environment"
	$(REMOVE_VENV)

environment-test: ## Test python environment is setup correctly
	$(PYTHON) test_environment.py

# IPyKernel

ipykernel-install: ## Creates an IPyKernel for this project's environment.
	$(PYTHON) -m ipykernel install --user --name $(IPYK_NAME) --display-name "$(IPYK_DISPLAY_NAME)"

ipykernel-uninstall: ## Removes the IPyKernel for this project's environment.
	jupyter kernelspec remove $(IPYK_NAME)

# Cleaning

clean: ## Delete all compiled Python files or temp files
	@rm -rf $(GARBAGE)

clean-data: ## Deletes any processed data files/cooked data files
	@echo ">>> Removing interim data files"
	@rm -rf data/interim/*
	@echo ">>> Removing processed data files"
	@rm -rf data/processed/*
	@echo ">>> Removing cooked data files"
	@rm -rf data/cooked/*

clean-media: ## Removes any generated media files
	@echo ">>> Removing all media files"
	@rm -rf media/*.*

clean-tensorflow: ## Removes log artifacts
	@echo ">>> Removing all TensorFlow logs"
	@rm -rf logs/*

# Code

lint: ## Lint using flake8
	flake8 --exclude=env/,lib/,bin/,docs/conf.py .

test: ## Run the unit tests over the project
	$(UNIT_TEST) tests/

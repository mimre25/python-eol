# python-eol
A simple tool to check if the current running python version is beyond or close to end of life (eol).

Warns 60 days before eol, and errors when using a python version that is beyond eol.

## Motivation
We tend to often forget which python version we are using for a project and that those version eventually will not get security updates once they are beyond eol.
This tool can be used to check this, for example, in a CI/CD system or as a pre-commit hook.

## Installation
```sh
pip install python-eol
```

## Usage
Simply invoke `eol` from your command line
```sh
eol
```
**Options**:
```sh
usage: eol [-h] [--fail-close-to-eol] [--check-docker-files] [--nep29]

eol check if your python version is beyond end of life

options:
  -h, --help            show this help message and exit
  --fail-close-to-eol   Fail if the python version is close to eol instead of just warn
  --check-docker-files  Search for Dockerfile (**/*Dockerfile*) and check the python versions specified inside them
  --nep29               Use NEP0029 end of life policy
```

## Pre-commit-hook
Add the following to your `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/mimre25/python-eol/
    rev: v0.0.3
    hooks:
      - id: python-eol-check
```

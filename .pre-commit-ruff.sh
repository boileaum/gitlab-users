#!/bin/bash
# Script pre-commit pour Ruff avec comportement conditionnel
# --fix en local, --diff en CI

if [ "$CI" = "true" ] || [ "$GITHUB_ACTIONS" = "true" ]; then
    # En CI: vérifier seulement, ne pas corriger
    exec ruff check --diff "$@"
else
    # En local: corriger automatiquement
    exec ruff check --fix "$@"
fi

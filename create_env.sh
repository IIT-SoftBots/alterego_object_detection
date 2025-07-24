#!/bin/bash

# Nome dell'ambiente da creare
ENV_NAME="object_detection_test"

# Percorso del file requirements.txt
REQUIREMENTS_FILE="requirements.txt"

# Controlla se il file requirements.txt esiste
if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "Errore: $REQUIREMENTS_FILE non trovato."
  exit 1
fi

# Source Conda (necessario per usare `conda activate` negli script)
source "$(conda info --base)/etc/profile.d/conda.sh"

# Crea l'ambiente Conda
echo "Creazione dell'ambiente Conda: $ENV_NAME"
conda create --name "$ENV_NAME" --yes python=3.10

# Esegui un nuovo subshell con l'ambiente attivo per installare i pacchetti
echo "Installazione dei pacchetti da $REQUIREMENTS_FILE"
conda run -n "$ENV_NAME" pip install -r "$REQUIREMENTS_FILE"

echo "Ambiente $ENV_NAME creato e configurato con successo."

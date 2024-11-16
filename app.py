import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os
import json
import base64

# Charger les informations d'identification depuis la variable d'environnement (base64)
encoded_json_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")

# Vérifier si les identifiants sont présents
if not encoded_json_credentials:
    st.error("Les informations d'identification Google Sheets sont manquantes dans les variables d'environnement.")
    raise Exception("Google Sheets credentials missing.")

# Décoder la chaîne base64 pour obtenir le fichier JSON
decoded_json = base64.b64decode(encoded_json_credentials)

# Convertir la chaîne JSON décodée en dictionnaire
credentials_dict = json.loads(decoded_json)

# Portée de l'API Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Charger les informations d'identification à partir du dictionnaire
creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)

# Autoriser l'accès via gspread
client = gspread.authorize(creds)

# Lire les données de Google Sheets
def get_data_from_sheets(sheet_id, sheet_name):
    # Utilisation de 'client' déjà autorisé pour accéder aux données
    sheet = client.open_by_key(sheet_id).worksheet(sheet_name)

    # Obtenir toutes les données de la feuille
    data = sheet.get_all_records()

    # Convertir les données en DataFrame
    df = pd.DataFrame(data)
    return df

# Application Streamlit
def app():
    st.title("Application de Visualisation des Données Clients")

    # Demander l'ID de la feuille Google Sheets
    sheet_id = st.text_input("Entrez l'ID de votre Google Sheets:", "")

    # Demander le nom de la feuille dans le fichier Google Sheets
    sheet_name = st.text_input("Entrez le nom de la feuille (onglet) à afficher:", "Sheet1")

    if sheet_id and sheet_name:
        try:
            # Charger les données de la feuille Google Sheets
            df = get_data_from_sheets(sheet_id, sheet_name)
            st.write("Données de la feuille sélectionnée :", df)

            # Proposer une colonne pour filtrer les valeurs
            column_to_filter = st.selectbox("Choisissez la colonne pour filtrer les valeurs :", df.columns)

            # Sélectionner des valeurs spécifiques pour filtrer les données
            unique_values = df[column_to_filter].unique()
            selected_value = st.selectbox("Choisissez une valeur à afficher :", unique_values)

            # Afficher les données filtrées
            filtered_df = df[df[column_to_filter] == selected_value]
            st.write(f"Données filtrées par {column_to_filter} = {selected_value} :", filtered_df)

        except Exception as e:
            st.error(f"Erreur : {e}")

# Lancer l'application Streamlit
if __name__ == "__main__":
    app()

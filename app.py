import streamlit as st
import pandas as pd
import os
import json
import base64
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Charger les informations d'identification depuis la variable d'environnement (base64)
encoded_json_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")

# Vérifier si les identifiants sont présents
if not encoded_json_credentials:
    st.error("Les informations d'identification Google Sheets sont manquantes dans les variables d'environnement.")
    raise Exception("Google Sheets credentials missing.")

# Correction du padding Base64 (si nécessaire)
padding = len(encoded_json_credentials) % 4
if padding != 0:
    encoded_json_credentials += "=" * (4 - padding)

try:
    # Décoder la chaîne base64 pour obtenir le fichier JSON
    decoded_json = base64.b64decode(encoded_json_credentials)
    credentials_dict = json.loads(decoded_json)
except Exception as e:
    st.error(f"Erreur lors du décodage des informations d'identification : {e}")
    raise

# Définir les étendues (scopes) nécessaires pour accéder aux Google Sheets
scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Charger les informations d'identification à partir du dictionnaire
credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)

# Créer le service API Google Sheets
service = build('sheets', 'v4', credentials=credentials)

# Fonction pour obtenir des données depuis Google Sheets
def get_data_from_sheets(sheet_id, sheet_name):
    """
    Récupère les données d'une feuille Google Sheets et les convertit en DataFrame.
    Utilise la première ligne comme en-tête pour les noms de colonnes.
    Remplace les valeurs manquantes par None.
    """
    try:
        # Construire la plage à partir du nom de la feuille
        range_name = f"{sheet_name}"

        # Récupérer les données de la feuille
        result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
        values = result.get('values', [])

        # Vérifier si des données existent
        if not values:
            return pd.DataFrame()  # Aucune donnée trouvée

        # Utiliser la première ligne comme noms de colonnes
        df = pd.DataFrame(values[1:], columns=values[0])

        # Remplir les cellules manquantes avec None
        df.fillna(value=None, inplace=True)

        return df

    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return pd.DataFrame()

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

            if df.empty:
                st.warning("Aucune donnée trouvée dans la feuille. Vérifiez l'ID et le nom de la feuille.")
            else:
                st.subheader("Données de la feuille sélectionnée :")
                st.dataframe(df)

                # Proposer une colonne pour filtrer les valeurs
                column_to_filter = st.selectbox("Choisissez la colonne pour filtrer les valeurs :", df.columns)

                # Remplacer les valeurs manquantes par 'None' dans la colonne choisie
                df[column_to_filter] = df[column_to_filter].replace("", None)

                # Sélectionner des valeurs spécifiques pour filtrer les données
                unique_values = df[column_to_filter].unique()  # Inclut les valeurs None
                selected_value = st.selectbox("Choisissez une valeur à afficher :", unique_values)

                # Afficher les données filtrées
                filtered_df = df[df[column_to_filter] == selected_value]
                st.subheader(f"Données filtrées par {column_to_filter} = {selected_value} :")
                st.dataframe(filtered_df)

        except Exception as e:
            st.error(f"Erreur : {e}")

# Lancer l'application Streamlit
if __name__ == "__main__":
    app()


# streamlit run app.py
import os
import base64
import json
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import matplotlib.pyplot as plt
import seaborn as sns

# Récupération des identifiants et de l'ID de la feuille depuis les variables d'environnement
encoded_json_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
spreadsheet_id = os.environ.get("SPREADSHEET_ID")

# Vérification des variables d'environnement
if not encoded_json_credentials:
    st.error("Les informations d'identification Google Sheets sont manquantes dans les variables d'environnement.")
    raise Exception("Google Sheets credentials missing.")

if not spreadsheet_id:
    st.error("L'ID de la feuille Google Sheets est manquant dans les variables d'environnement.")
    raise Exception("Spreadsheet ID missing.")

# Décodage des identifiants
padding = len(encoded_json_credentials) % 4
if padding != 0:
    encoded_json_credentials += "=" * (4 - padding)

try:
    decoded_json = base64.b64decode(encoded_json_credentials)
    credentials_dict = json.loads(decoded_json)
except Exception as e:
    st.error(f"Erreur lors du décodage des informations d'identification : {e}")
    raise

# Connexion aux services Google Sheets
try:
    credentials = Credentials.from_service_account_info(credentials_dict)
    service = build('sheets', 'v4', credentials=credentials)
    st.success("Connexion réussie aux services Google Sheets.")
except Exception as e:
    st.error(f"Erreur lors de la création des credentials ou de la connexion : {e}")
    raise

# Fonction pour récupérer les données d'une feuille spécifique
def get_data_from_sheet(sheet_name):
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=sheet_name).execute()
        values = result.get("values", [])

        if values:
            # Convertir les données en DataFrame
            df = pd.DataFrame(values[1:], columns=values[0])  # Utiliser la première ligne comme noms de colonnes
            df.fillna("Non spécifié", inplace=True)  # Remplacer les cellules vides
            return df
        else:
            return pd.DataFrame()  # Retourner un DataFrame vide si aucune donnée n'existe
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return pd.DataFrame()

# Fonction d'analyse des sous-ensembles de type_mail
def analyse_type_mail(df):
    if df.empty:
        st.warning("Aucune donnée disponible pour l'analyse.")
        return

    type_mail_categories = [
        "Envoi de carte verte",
        "Envoi de devis",
        "Message de demande de documents",
        "Message de rappel d'injoignabilité",
        "Message de suivi de devis"
    ]

    for category in type_mail_categories:
        filtered_df = df[df['type_mail'] == category]
        if not filtered_df.empty:
            count_per_courtier = filtered_df.groupby('courtier')['type_mail'].count().reset_index()
            count_per_courtier.columns = ['Courtier', f'Nombre_{category.replace(" ", "_")}']
            count_per_courtier = count_per_courtier.sort_values(by=f'Nombre_{category.replace(" ", "_")}', ascending=False)

            st.subheader(f"Analyse pour '{category}'")
            st.dataframe(count_per_courtier)
        else:
            st.warning(f"Aucune donnée pour '{category}'.")

# Fonction de comparaison des courtiers par type_mail
def compare_courtiers_by_type_mail(df):
    if df.empty:
        st.warning("Aucune donnée disponible pour la comparaison.")
        return

    comparison_df = df.groupby(['courtier', 'type_mail']).size().reset_index(name='Nombre_envois')

    st.subheader("Comparaison des courtiers par type_mail")
    st.dataframe(comparison_df)

    plt.figure(figsize=(10, 6))
    sns.barplot(data=comparison_df, x='courtier', y='Nombre_envois', hue='type_mail', palette="Set2")
    plt.title("Comparaison des courtiers par type_mail")
    plt.xlabel("Courtier")
    plt.ylabel("Nombre d'envois")
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(plt)

# Application Streamlit
def app():
    st.title("Application de Visualisation des Données Clients")

    st.sidebar.title("Analyse des données")
    analyse_button = st.sidebar.button("Analyse robuste : Activité des courtiers par type_mail")
    compare_button = st.sidebar.button("Comparer les courtiers par type_mail")

    sheet_name = st.text_input("Entrez le nom de la feuille (onglet) à afficher :", "message_de_suivis_devis")

    if st.button("Afficher les données"):
        if sheet_name:
            df = get_data_from_sheet(sheet_name)
            if df.empty:
                st.warning("Aucune donnée trouvée dans l'onglet. Vérifiez le nom.")
            else:
                st.subheader("Données de l'onglet sélectionné :")
                st.dataframe(df)

                column_to_filter = st.selectbox("Choisissez la colonne pour filtrer les valeurs :", df.columns)
                if column_to_filter:
                    df[column_to_filter] = df[column_to_filter].astype(str)  # Convertir explicitement en chaîne
                    unique_values = df[column_to_filter].unique()
                    selected_value = st.selectbox("Choisissez une valeur à afficher :", unique_values)
                    filtered_df = df[df[column_to_filter] == selected_value]
                    st.subheader(f"Données filtrées par {column_to_filter} = {selected_value} :")
                    st.dataframe(filtered_df)

    if analyse_button:
        df = get_data_from_sheet(sheet_name)
        analyse_type_mail(df)

    if compare_button:
        df = get_data_from_sheet(sheet_name)
        compare_courtiers_by_type_mail(df)

if __name__ == "__main__":
    app()

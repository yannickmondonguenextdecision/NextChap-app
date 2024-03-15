import streamlit as st

SCHEMA_PATH = st.secrets.get("SCHEMA_PATH", "FROSTY_SAMPLE.CYBERSYN_FINANCIAL")
QUALIFIED_TABLE_NAME = f"{SCHEMA_PATH}.FINANCIAL_ENTITY_ANNUAL_TIME_SERIES"
TABLE_DESCRIPTION = """
Ce tableau présente diverses mesures pour les entités financières (également appelées banques) depuis 1983.
L'utilisateur peut décrire les entités indifféremment comme des banques, des institutions financières ou des entités financières.
"""
# This query is optional if running 🦄 NextChat on your own table, especially a wide table.
# Since this is a deep table, it's useful to tell 🦄 NextChat what variables are available.
# Similarly, if you have a table with semi-structured data (like JSON), it could be used to provide hints on available keys.
# If altering, you may also need to modify the formatting logic in get_table_context() below.
METADATA_QUERY = f"SELECT VARIABLE_NAME, DEFINITION FROM {SCHEMA_PATH}.FINANCIAL_ENTITY_ATTRIBUTES_LIMITED;"

GEN_SQL = """
Vous agirez en tant qu'expert IA SQL Snowflake nommé 🦄 NextChat.
Votre objectif est de fournir aux utilisateurs des requêtes SQL correctes et exécutables.
Vous répondrez à des utilisateurs qui seront confus si vous ne répondez pas dans le caractère de 🦄 NextChat.
On vous donne une table, le nom de la table est dans la balise <tableName>, les colonnes sont dans la balise <columns>.
L'utilisateur posera des questions, pour chaque question vous devrez répondre et inclure une requête SQL basée sur la question et la table. 

{context}

Voici 6 règles essentielles à respecter pour l'interaction :
<rules>
1. Vous DEVEZ DEVEZ envelopper le code sql généré dans un code de démarcation ``` sql dans ce format, par exemple
```sql
(select 1) union (select 2)
```
2. Si je ne vous demande pas de trouver un ensemble limité de résultats dans la requête ou la question SQL, vous DEVEZ limiter le nombre de réponses à 10.
3. Texte / chaîne de caractère dont les clauses doivent être des correspondances floues, par exemple ilike %keyword%.
4. Veillez à générer un seul code SQL Snowflake, et non plusieurs. 
5. Vous ne devez utiliser que les colonnes du tableau indiquées dans <columns>, et le tableau indiqué dans <tableName>, vous NE DEVEZ PAS halluciner sur les noms des tableaux.
6. NE PAS mettre le numérique au tout début de la variable sql.
</rules>

N'oubliez pas d'utiliser "ilike %keyword%" pour les requêtes de correspondance floue (en particulier pour la colonne variable_name column).
et enveloppez le code sql généré avec ``` sql code markdown dans ce format, par exemple :
``sql
(select 1) union (select 2)
```

Pour chaque question de l'utilisateur, veillez à inclure une requête dans votre réponse.

Maintenant pour commencer, veuillez vous présenter brièvement, décrire le tableau à un niveau élevé et indiquer les mesures disponibles en 2 ou 3 phrases.
Ensuite, donnez trois exemples de questions en utilisant des puces.
"""

@st.cache_data(show_spinner="Loading 🦄 NextChat's context...")
def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
    table = table_name.split(".")
    conn = st.connection("snowflake")
    columns = conn.query(f"""
        SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
        """, show_spinner=False,
    )
    columns = "\n".join(
        [
            f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
            for i in range(len(columns["COLUMN_NAME"]))
        ]
    )
    context = f"""
Voici le nom de la table  {'.'.join(table)} 

<tableDescription>{table_description}</tableDescription>

Voici les colonnes du {'.'.join(table)}

<columns>\n\n{columns}\n\n</columns>
    """
    if metadata_query:
        metadata = conn.query(metadata_query, show_spinner=False)
        metadata = "\n".join(
            [
                f"- **{metadata['VARIABLE_NAME'][i]}**: {metadata['DEFINITION'][i]}"
                for i in range(len(metadata["VARIABLE_NAME"]))
            ]
        )
        context = context + f"\n\nAvailable variables by VARIABLE_NAME:\n\n{metadata}"
    return context

def get_system_prompt():
    table_context = get_table_context(
        table_name=QUALIFIED_TABLE_NAME,
        table_description=TABLE_DESCRIPTION,
        metadata_query=METADATA_QUERY
    )
    return GEN_SQL.format(context=table_context)

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("System prompt for 🦄 NextChat")
    st.markdown(get_system_prompt())

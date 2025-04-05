import os
import sqlite3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai

# App Title
title = st.title("CSV TO SQL CONVERTER")
db_name = " "

# File Upload Section
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    # Read the CSV file into a DataFrame
    data = pd.read_csv(uploaded_file)
    st.write("Preview of the CSV file:")
    st.write(data)

    # Prompt user for database name and table name
    db_name = st.text_input("Enter the SQLite database name (e.g., my_database.db):")
    table_name = st.text_input("Enter the table name to save the data:", key="table_name_save")

    if st.button("Convert to SQL"):
        if not db_name:  # Check if db_name is empty
            st.error("Please enter a valid database name!")
        elif not table_name:  # Check if table_name is empty
            st.error("Please enter a valid table name!")
        elif not os.path.exists(db_name):
            st.error("Database does not exist. Please check the name or path!")
        else:
            # Connect to SQLite database
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()

            # Save DataFrame to the specified SQL table
            data.to_sql(table_name, conn, if_exists="replace", index=False)
            conn.close()
            st.success(f"Data has been successfully saved to the table '{table_name}' in the SQLite database: {db_name}")

# Database Query Section
db_name_query = st.text_input("Enter SQLite database name to check records:", key="db_check")
table_name_query = st.text_input("Enter the table name to display records:", key="table_check")

if st.button("Check Database & Display Records"):
    if not db_name_query:  # Check if db_name_query is empty
        st.error("Please enter a valid database name!")
    elif not table_name_query:  # Check if table_name_query is empty
        st.error("Please enter a valid table name!")
    elif not os.path.exists(db_name_query):
        st.error("The specified database does not exist!")
    else:
        try:
            conn = sqlite3.connect(db_name_query)
            cursor = conn.cursor()

            # Check if table exists in the database
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name_query}';")
            table_exists = cursor.fetchone()

            if table_exists:
                st.success(f"Table '{table_name_query}' exists in the database.")
                
                # Retrieve and display all records from the table
                cursor.execute(f"SELECT * FROM {table_name_query};")
                rows = cursor.fetchall()
                
                if rows:
                    st.write(f"Records in the table exists'{table_name_query}':")
                else:
                    st.warning(f"The table '{table_name_query}' is empty.")
            else:
                st.error(f"Table '{table_name_query}' does not exist in the database.")

            conn.close()
        except sqlite3.Error as e:
            st.error(f"SQLite error occurred: {e}")

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

#Function to load model and get query and answer as response
def google_gemini_response(question,prompt):
    model= genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([prompt[0],question])
    return response.text

#Function to retrieve query from SQL database
def read_sql_query(sql,db):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        print(f"SQL query: {sql}")
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.commit()
        conn.close()
        return rows
    
    except sqlite3.Error as e:
        print(f"SQLite error occurred: {e}")
        return None


prompt = ["""
        
 You are an expert in converting English questions to SQL query!
    The SQL database has the name"""+db_name+
     """ and has its own columns -
     \n\nFor example,\nExample 1 - How many entries of records are present?, 
    the SQL command will be something like this SELECT COUNT(*) FROM"""+db_name+""" ;
    \nExample 2 - Tell me counts by Gender who survived, 
    the SQL command will be something like this SELECT GENDER, COUNT(*) FROM"""+db_name+""" 
   GROUP BY GENDER HAVING SURVIVED=1;
    also the sql code should not have ``` in beginning or end and sql word in output
"""]

#Streamlit App

question = st.text_input('Ask a question', key='input')
submit = st.button("Submit the Question")

if submit:
    try:
        response = google_gemini_response(question,prompt)
        st.subheader(f"Generated SQL code: {response}")
        data = read_sql_query(response, db_name)
        if data:
            for row in data:
                st.write(row)
                print(data)
        else:
            print("The query did not return any results. Please verify your inputs.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


    



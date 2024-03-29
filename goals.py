import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from datetime import datetime, timedelta
import json  
import re
import streamlit_shadcn_ui as ui
from google.oauth2 import service_account
from local_components import card_container

# Define your Google Sheets credentials JSON file (replace with your own)
credentials_path = 'dreamteam-410510-f5750e00bbd9.json'
    
# Authenticate with Google Sheets using the credentials
credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=['https://spreadsheets.google.com/feeds'])
    
# Authenticate with Google Sheets using gspread
gc = gspread.authorize(credentials)
    
# Your Google Sheets URL
url = "https://docs.google.com/spreadsheets/d/1c9ZVdhfrTDME7wjCgxkDeb7GRzgg43JCJPP3D_C__to/edit#gid=0"
    
# Open the Google Sheets spreadsheet
worksheet = gc.open_by_url(url).worksheet("finances")
worksheet_budget = gc.open_by_url(url).worksheet("budget")

 # Read data from the Google Sheets worksheet
data_frame = worksheet.get_all_values()
budget = worksheet_budget.get_all_values()
    
# Prepare data for Plotly
headers = data_frame[0]
headers_2 = budget[0]
data_frame = data_frame[1:]
budget = budget[1:]

df = pd.DataFrame(data_frame, columns=headers)
df2 = pd.DataFrame(budget, columns=headers_2)

df['Amount'] = df['Amount'].astype(int)
df2['Amount'] = df2['Amount'].astype(int)

# Regular expression to capture date values in the format YYYY-MM-DD
date_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

df['Purchase Date'] = df['Date'].str.extract(date_pattern)
df2['Date'] = df2['Date'].str.extract(date_pattern)


df['Purchase Date'] = pd.to_datetime(df['Purchase Date'])
df2['Date'] = pd.to_datetime(df2['Date'])

df['Month'] = df['Purchase Date'].dt.month_name()
df2['Month'] = df2['Date'].dt.month_name()

df['Day'] = df['Purchase Date'].dt.day_name()


newdf = df[['Purchase Date', 'Use', 'Category', 'Store', 'Amount']]

current_date = datetime.now()
timestamp = pd.Timestamp(current_date)
current_month = timestamp.strftime('%B')

this_month = df[df['Month'] == current_month]
this_month2 = df2[df2['Month'] == current_month]

amount_month = this_month[this_month['Amount']>0]['Amount'].sum()
amount = "{:,.0f}".format(amount_month)

start_of_week = current_date - timedelta(days=current_date.weekday())
end_of_week = start_of_week + timedelta(days=6)
this_week = df[((df['Purchase Date']).dt.date >= start_of_week.date()) & ((df['Purchase Date']).dt.date <= end_of_week.date())]

week_amount = this_week[this_week['Amount']>0]['Amount'].sum()
this_week_amount = "{:,.0f}".format(week_amount)

frequent_use = df['Use'].mode().values[0]
count_store = df[df['Use'] == frequent_use].shape[0]


st.set_page_config(page_icon="myprofile.jpg", page_title = 'dreamteam', layout="wide")

# st.sidebar.image('myprofile.jpg', use_column_width=True)


# st.sidebar.subheader("Navigation Pane")


with card_container(key='global'):
    tab1, tab2, tab3= st.tabs(["📈 Expenditure Summary", "New Entry", "🗃 Records"])
    with tab1:
        with card_container(key='dashboard'):
            cols = st.columns(3)
            with cols[0]:
                ui.metric_card(title="Month To Date", content=f'Ksh. {amount}',  key="card1")
            with cols[1]:
                ui.metric_card(title="Week To Date", content=f'Ksh. {this_week_amount}',  key="card2")
            with cols[2]:
                ui.metric_card(title="Frequent Purchase", content = f'{frequent_use}', description= f"{count_store} times", key="card3")


        with card_container(key='graph'):
            tab4, tab5  = st.tabs(["Month Analysis", "This Week Analysis"])
            with tab4:
                # Calculate the sum of amounts for each category
                bar_actual = this_month.groupby('Category')['Amount'].sum().reset_index()
                bar_budget = this_month2.groupby('Category')['Amount'].sum().reset_index()

                fig = go.Figure()

                fig.add_trace(go.Bar(
                        width= 0.425,
                        x= bar_actual['Category'],
                        y= bar_actual['Amount'],   
                        name = 'Actual',
                        marker_color="#00A550"
                           
                        ))               
                
                
                fig.add_trace(go.Bar(
                        width= 0.425,
                        x= bar_budget['Category'],
                        y= bar_budget['Amount'], 
                        name = 'Budget',                                
                        marker_color="#FFA836"   
                        ))
                
                
                
                fig.update_layout(title={'text': 'MONTHLY EXPENDITURE ANALYSIS', 'x': 0.5, 'xanchor': 'center'},  width=900,
                                        xaxis_title='Category',
                                        yaxis_title='Amount',
                                        xaxis=dict(tickfont=dict(size=7)),                                  
                                        )

                st.plotly_chart(fig)
            
            with tab5:
                day_amounts = this_week.groupby('Day')['Amount'].sum()
            
                # Create a bar chart for Category vs. Sum of Amounts using Plotly
                fig2 = go.Figure(data=[go.Bar(
                x=day_amounts.index,
                y=day_amounts        
                )])
                
                fig2.update_layout(title={'text': 'THIS WEEK EXPENDITURE BY DAY OF WEEK', 'x': 0.5, 'xanchor': 'center'}, width=900,
                                    xaxis=dict(categoryorder='array', categoryarray=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], tickfont=dict(size=10)),
                                    xaxis_title='Day',
                                    yaxis_title='Amount'                              
                                )
                
                
                
                st.plotly_chart(fig2)


    with tab2:
        with card_container(key='form'):
        
            # Create a form to input data for the new entry
            
            Date = json.dumps(st.date_input("Date"), default=str)
            Use = st.text_input("Product")
            Category = st.selectbox("Category:", ["SAVINGS", "HOUSE", "FOOD", "FAMILY", "TRANSPORT", "EDUCATION", "ENTERTAINMENT", "APPEARANCE", "MISCELLANEOUS", "TITHE", "DEBT"])        
            Store = st.text_input("Store")
            Amount = st.text_input("Amount")

            if st.button("Add Entry"):
                # Create a new row of data to add to the Google Sheets spreadsheet
                new_data = [Date, Use, Category, Store, Amount]

                # Append the new row of data to the worksheet
                worksheet.append_row(new_data) 

                st.success("Data submitted successfully!")

    with tab3:
        
        st.table(newdf)
      



           

import streamlit as st
import pandas as pd
from MongoDB import mdb
import datetime

st.set_page_config(page_title='Compare Stock and Index')

#@st.chache
def find_asset_options(mdb):
    return list(mdb.client['gestao']['asset.prices'].distinct('_id.asset_id'))

#@st.chache
def mongo_import_to_df(mdb, assets: list, start_date, end_date):
    list_dict = []
    query = {
        '_id.asset_id': {
            '$in': assets
            },
        '_id.date': {
        '$gte': start_date,
        '$lte': end_date}
    }
        
    for doc in mdb.client['gestao']['asset.prices'].find(query):
        dict_i = {}
        try:
            dict_i['date'] = doc['_id']['date']
        except:
            dict_i['date'] = 'NA'
        try:
            dict_i['asset'] = doc['_id']['asset_id']
        except:
            dict_i['asset'] = 'NA'
        try:
            dict_i['close'] = doc['close']
        except:
            dict_i['close'] = 'NA'

        list_dict.append(dict_i)
    df = pd.DataFrame(list_dict)
    df = df[~(df['close'] == 'NA')]
    return df

def percentage_change_from_min(group):
    # Find the price at the minimum date for the group
    min_date_price = group.loc[group['date'].idxmin(), 'close']
    
    # Calculate the percentage change for each row compared to the minimum date
    group['pct_change'] = ((group['close'] - min_date_price) / min_date_price) * 100
    return group


# Initialize session state for dates
if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.datetime(2010, 1, 1)
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.datetime.today()
if 'last_start_date' not in st.session_state:
    st.session_state.last_start_date = st.session_state.start_date
if 'last_end_date' not in st.session_state:
    st.session_state.last_end_date = st.session_state.end_date



with st.container():
    st.title('Graph')
    
    select_options = find_asset_options(mdb)
    chosen_assets = st.multiselect("Select index or stock:", select_options)

    # Store the new values in session_state when slider changes
    st.session_state.last_start_date,st.session_state.last_end_date = st.slider(
        'Select period:',
        min_value=st.session_state.start_date,
        max_value=st.session_state.end_date,
        value=(st.session_state.last_start_date, st.session_state.last_end_date),
        step=datetime.timedelta(days=1)
    )
    

    if chosen_assets:
        df_selected = mongo_import_to_df(mdb, chosen_assets,st.session_state.last_start_date, st.session_state.last_end_date)
        df_selected['date'] = pd.to_datetime(df_selected['date'])
        df_selected = df_selected.sort_values(by = 'date', ascending= False)
        df_selected = df_selected.groupby('asset').apply(percentage_change_from_min, include_groups=False).reset_index()
        df_pivot = df_selected.pivot_table(values = 'pct_change',columns = ['asset'], index = 'date').reset_index()
        st.line_chart(data=df_pivot, y=chosen_assets, x='date')




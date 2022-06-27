import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

st.set_page_config(
   page_title="Análisis de enlaces",
   layout="wide"
)


st.title("Análisis de enlaces")
@st.cache
def getInlinksPorURL(df):
    df_agrupado=df.groupby(['Destination','Follow','Status Code']).count()['Source'].reset_index(name="count")
    df_follow=df_agrupado[df_agrupado['Follow']==True]
    df_nofollow=df_agrupado[df_agrupado['Follow']==False]
    df_2=df_agrupado[["Destination", "Status Code"]].drop_duplicates()
    result=df_2.merge(df_follow,left_on=["Destination", "Status Code"], right_on=["Destination", "Status Code"], how="left")
    result=result.merge(df_nofollow,left_on=["Destination", "Status Code"], right_on=["Destination", "Status Code"], how="left")
    result.rename(columns={"count_x":"Count Follow","count_y":"Count Nofollow"}, inplace=True)
    result=result[["Destination","Status Code","Count Follow", "Count Nofollow"]].sort_values(by='Count Follow', ascending=False).reset_index(drop=True)
    result['Count Follow'] = result['Count Follow'].fillna(0).astype(int)
    result['Count Nofollow'] = result['Count Nofollow'].fillna(0).astype(int)
    return result

f_entrada=st.file_uploader('CSV con datos exportados de Screaming Frog (all_inlinks.csv)', type='csv')
if f_entrada is not None:
    df_filtrado=pd.read_csv(f_entrada)
    df_mask=(df_filtrado['Type']=='Hyperlink')&(df_filtrado['Link Position']=='Content')&(df_filtrado['Source']!=df_filtrado['Destination'])
    df_filtrado=df_filtrado[df_mask]
    
    result=getInlinksPorURL(df_filtrado)
    

    gb=GridOptionsBuilder.from_dataframe(result)
    gb.configure_pagination()
    gb.configure_side_bar()
    #sel_mode=st.radio('Selection type', options=['single','multiple'])   
    gb.configure_selection(selection_mode='multiple',use_checkbox=True)
    gb.configure_default_column(groupable=True, enableRowGroup=True, aggFunc="count")
    gridoptions=gb.build()
    st.subheader('Resumen de enlaces')
    grid_table=AgGrid(result,height=600,gridOptions=gridoptions,update_mode=GridUpdateMode.SELECTION_CHANGED,enable_enterprise_modules=True)  
    sel_rows=grid_table['selected_rows']
    #st.write(sel_rows)
    if len(sel_rows) > 0:
        #Filtramos la URL seleccionada en el dataframe con todos los enlaces
        filtro=[]
        for i in sel_rows:
            destino=i["Destination"]
            filtro.append(destino)
        df = df_filtrado.drop(columns=["Type","Size (Bytes)","Status","Target","Path Type","Link Position"])
        boolean_series = df["Destination"].isin(filtro) 
        df=df[boolean_series]
        gb_enlaces=GridOptionsBuilder.from_dataframe(df)
        gb_enlaces.configure_side_bar()
        gb_enlaces.configure_default_column(groupable=True, enableRowGroup=True, aggFunc="count", editable=True)
        gridoptions_enlaces=gb_enlaces.build()
        st.subheader('Enlaces apuntando a destinos seleccionados')
        grid_table_enlaces=AgGrid(df,gridOptions=gridoptions_enlaces,enable_enterprise_modules=True)

 
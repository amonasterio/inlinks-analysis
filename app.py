import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from st_aggrid import AgGrid, GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

st.set_page_config(
   page_title="Análisis de enlaces",
   layout="wide"
)


st.title("Análisis de enlaces")

@st.cache
def getRutaDominio(url):
    parsed = urlparse(url)
    absolute_rute=parsed.scheme+'://'+parsed.netloc
    return absolute_rute

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

@st.cache
def getOportunidades(df_oportunidades,ruta_abosoluta):
    df_salida=None
    if df_oportunidades is not None:
        list_keywords = df_oportunidades.values.tolist()
        list_urls = []
        for x in list_keywords:
            list_urls.append(x[6])
        #Todas las URL que rankean 
        list_urls = list(dict.fromkeys(list_urls))
        list_keyword_url = []
        for x in list_keywords:
            list_keyword_url.append([x[6],x[0],x[1],x[3]])

        absolute_rute=ruta_abosoluta
        internal_linking_opportunities = []
        for iteration in list_urls:
        
            page = requests.get(iteration)
      
            soup = BeautifulSoup(page.text, 'html.parser')
            paragraphs = soup.find_all('p')
            paragraphs = [x.text for x in paragraphs]
            
            links = []
            for link in soup.findAll('a'):
                links.append(link.get('href'))
            
            for x in list_keyword_url:
                for y in paragraphs:
                    kw_compara=" " + x[1].lower() + " "
                    compara=" " + y.lower().replace(",","").replace(".","").replace(";","").replace("?","").replace("!","") + " "
                    if kw_compara in compara and iteration != x[0]:
                        links_presence = False
                        for z in links:
                            try:
                                if x[0].replace(absolute_rute,"") == z.replace(absolute_rute,""):
                                    links_presence = True
                            except AttributeError:
                                pass

                        if links_presence == False:
                            internal_linking_opportunities.append([x[1],y,iteration,x[0], "False", x[2],x[3]])
                        else:
                            internal_linking_opportunities.append([x[1],y,iteration,x[0], "True", x[2],x[3]]) 
        df_salida=pd.DataFrame(internal_linking_opportunities, columns = ["Keyword", "Text", "Source URL", "Target URL", "Link Presence", "Keyword Position", "Search Volume"])
    return df_salida



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
        df["Rel"]=df["Rel"].fillna('').astype(str)
        df["Alt Text"]=df["Alt Text"].fillna('').astype(str)
        df["Anchor"]=df["Anchor"].fillna('').astype(str)
        boolean_series = df["Destination"].isin(filtro) 
        df=df[boolean_series]
        gb_enlaces=GridOptionsBuilder.from_dataframe(df)
        gb_enlaces.configure_side_bar()
        gb_enlaces.configure_default_column(groupable=True, enableRowGroup=True, aggFunc="count", editable=True)
        gridoptions_enlaces=gb_enlaces.build()
        st.subheader('Enlaces apuntando a destinos seleccionados')
        grid_table_enlaces=AgGrid(df,gridOptions=gridoptions_enlaces,enable_enterprise_modules=True)
        
        #Buscamos oportunidades de ampliar enlaces entrantes
        st.subheader('Posibilidad de inlinks')
        f_semrush=st.file_uploader('CSV con datos exportados de Semrush', type='csv')
        if f_semrush is not None:
            df_semrush=pd.read_csv(f_semrush)
            ruta_dominio=getRutaDominio(filtro[0])
            print(ruta_dominio)
            df_salida=getOportunidades(df_semrush,ruta_dominio)
            #Dejamos únicamente las URL que hemos seleccionado antes, ya que son en las que quermos generar enlaces
            boolean_oportunidades = df_salida["Target URL"].isin(filtro) 
            df_salida=df_salida[boolean_oportunidades]
            #lista_url_queremos_enlaces=df_oportunidades['URL'].to_list()
            AgGrid(df_salida)
            
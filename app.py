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
def getUrlSinEnlaces(df_html,inlinks_contenido):
    df_sin_enlaces=df_html[(~df_html["Address"].isin(inlinks_contenido))&(df_html["Status Code"]==200)]
    return df_sin_enlaces


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

def pintaTabla(df_pinta, grid_update, selection):
    gb=GridOptionsBuilder.from_dataframe(df_pinta)
    gb.configure_pagination()
    gb.configure_side_bar()  
    if selection:
        gb.configure_selection(selection_mode='multiple',use_checkbox=True)
    gb.configure_default_column(groupable=True, enableRowGroup=True, aggFunc="count")
    grid_options=gb.build()
    if grid_update:
        grid_table=AgGrid(df_pinta,gridOptions=grid_options,update_mode=GridUpdateMode.SELECTION_CHANGED,enable_enterprise_modules=True, editable=True)  
    else:
        grid_table=AgGrid(df_pinta,gridOptions=grid_options,enable_enterprise_modules=True, editable=True)  
    return grid_table

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



f_inlinks=st.file_uploader('CSV con datos exportados de Screaming Frog (all_inlinks.csv)', type='csv')
f_internal=st.file_uploader('CSV con datos exportados de Screaming Frog (internal_html.csv)', type='csv')
if f_inlinks is not None:
    if f_internal is not None:
        df_inlinks=pd.read_csv(f_inlinks)
        df_internal=pd.read_csv(f_internal)
  
        #filtramos para dejar únicamente enlaces en el contenido que apunten a URL distintas de la origen
        df_mask=(df_inlinks['Type']=='Hyperlink')&(df_inlinks['Link Position']=='Content')&(df_inlinks['Source']!=df_inlinks['Destination'])
        df_inlinks_contenido=df_inlinks[df_mask]
    
        l_inlinks_contenidos=df_inlinks_contenido["Destination"].to_list()
        df_url_sin_enlaces=getUrlSinEnlaces(df_internal,l_inlinks_contenidos)
        st.subheader('URL sin inlinks en contenido')
        grid_table_url_sin_enlaces=pintaTabla(df_url_sin_enlaces, True, True)
    
        st.subheader('Resumen de inlinks en contenido')
        df_resumen=getInlinksPorURL(df_inlinks_contenido)
        grid_table_resumen=pintaTabla(df_resumen, True, True) 
        
        sel_rows=grid_table_resumen['selected_rows']
        #st.write(sel_rows)
        if len(sel_rows) > 0:
            #Filtramos la URL seleccionada en el dataframe con todos los enlaces
            filtro=[]
            for i in sel_rows:
                destino=i["Destination"]
                filtro.append(destino)
            #Eliminamos columnas que no nos interesas
            df_inlinks_contenido = df_inlinks_contenido.drop(columns=["Type","Size (Bytes)","Status","Target","Path Type","Link Position"])
            df_inlinks_contenido["Rel"]=df_inlinks_contenido["Rel"].fillna('').astype(str)
            df_inlinks_contenido["Alt Text"]=df_inlinks_contenido["Alt Text"].fillna('').astype(str)
            df_inlinks_contenido["Anchor"]=df_inlinks_contenido["Anchor"].fillna('').astype(str)
            boolean_series = df_inlinks_contenido["Destination"].isin(filtro) 
            df_inlinks_seleccionados=df_inlinks_contenido[boolean_series]
            
            st.subheader('Enlaces apuntando a destinos seleccionados')

            grid_table_enlaces=pintaTabla(df_inlinks_seleccionados,False, False)
            

            #Buscamos oportunidades de ampliar enlaces entrantes
            #st.subheader('Posibilidad de inlinks')
            #f_semrush=st.file_uploader('CSV con datos exportados de Semrush', type='csv')
            #if f_semrush is not None:
                #df_semrush=pd.read_csv(f_semrush)
                #ruta_dominio=getRutaDominio(filtro[0])
                #print(ruta_dominio)
                #df_salida=getOportunidades(df_semrush,ruta_dominio)
                #Dejamos únicamente las URL que hemos seleccionado antes, ya que son en las que quermos generar enlaces
                #boolean_oportunidades = df_salida["Target URL"].isin(filtro) 
                #df_salida=df_salida[boolean_oportunidades]
         
                #AgGrid(df_salida)
                
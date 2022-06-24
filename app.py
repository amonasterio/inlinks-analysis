import pandas as pd
import streamlit as st


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
    tipo_filtro_url = st.radio(
     "Tipo de filtrado",
     ('Contiene','Igual a'))
    filtro_url=st.text_input("Introduzca URL que quiera filtrar")
    if tipo_filtro_url=="Igual a":
        df_mask_url=df_filtrado['Destination']==filtro_url
    else:
        df_mask_url=df_filtrado['Destination'].str.contains(filtro_url)
    df_filtrado=df_filtrado[df_mask_url]
    result=getInlinksPorURL(df_filtrado)
    st.dataframe(result)
    st.download_button(
                label="Descargar como CSV",
                data=result.to_csv(index = False).encode('utf-8'),
                file_name='agrupado.csv',
                mime='text/csv',
            )
    
    df = df_filtrado.drop(columns=["Type","Size (Bytes)","Status","Target","Path Type","Link Position"])
    url=st.text_input(label="Analizar URL")
    df_mask=df['Destination']==url
    df=df[df_mask]
    st.dataframe(df)
    st.download_button(
                label="Descargar como CSV",
                data=df.to_csv(index = False).encode('utf-8'),
                file_name='agrupado.csv',
                mime='text/csv',
            )
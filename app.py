
import streamlit as st
import zipfile
from io import StringIO
import pandas as pd
import spacy
from spacy.cli import download
download('en_core_web_sm')
nlp = spacy.load('en_core_web_sm')
from collections import Counter
from spacy.matcher import PhraseMatcher
import docx
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import os
import base64
import plotly.express as px 
##Fuctions

def getText(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)


def convert_pdf_to_txt(infile, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)
    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)
    #infile = open(path, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close()
    return text



def create_profile(file):
    if file_format in file:
        text = convert_pdf_to_txt(zf.open(file))
    else:
        text= getText(zf.open(file))
    text = str(text)
    text = text.replace("\\n", " ")
    text = text.lower()
    text = text.replace("\n", " ")
    text = text.replace("(", " ")
    text = text.replace(")"," ")
    #summary_resume= summarize(text, ratio=0.10)
    #below is the csv where we have all the keywords, you can customize your own
    keyword_dict = pd.read_csv('Keywords_2.csv')
    stats_words = [nlp(text) for text in keyword_dict['Statistics'].dropna(axis = 0)]
    NLP_words = [nlp(text) for text in keyword_dict['NLP'].dropna(axis = 0)]
    ML_words = [nlp(text) for text in keyword_dict['Machine Learning'].dropna(axis = 0)]
    DL_words = [nlp(text) for text in keyword_dict['Deep Learning'].dropna(axis = 0)]
    R_words = [nlp(text) for text in keyword_dict['R Language'].dropna(axis = 0)]
    python_words = [nlp(text) for text in keyword_dict['Python Language'].dropna(axis = 0)]
    Data_Engineering_words = [nlp(text) for text in keyword_dict['Data Engineering'].dropna(axis = 0)]
    Visualization_words = [nlp(text) for text in keyword_dict['Visualization'].dropna(axis = 0)]
    Web_scraping_words = [nlp(text) for text in keyword_dict['Web Scraping'].dropna(axis = 0)]

    matcher = PhraseMatcher(nlp.vocab)
    matcher.add('Statistics', None, *stats_words)
    matcher.add('NLP', None, *NLP_words)
    matcher.add('Machine_Learning', None, *ML_words)
    matcher.add('Deep_Learning', None, *DL_words)
    matcher.add('R', None, *R_words)
    matcher.add('Python', None, *python_words)
    matcher.add('Data_Engineering', None, *Data_Engineering_words)
    matcher.add('Visualization', None, *Visualization_words)
    matcher.add('Web_Scraping', None, *Web_scraping_words)
    
    doc = nlp(text)
    
    d = []  
    matches = matcher(doc)
    for match_id, start, end in matches:
        rule_id = nlp.vocab.strings[match_id]  # get the unicode ID, i.e. 'COLOR'
        span = doc[start : end]  # get the matched slice of the doc
        d.append((rule_id, span.text))      
    keywords = "\n".join(f'{i[0]} {i[1]} ({j})' for i,j in Counter(d).items())
    #print(text)
    ## convertimg string of keywords to dataframe
    df = pd.read_csv(StringIO(keywords),names = ['Keywords_List'])
    df1 = pd.DataFrame(df.Keywords_List.str.split(' ',1).tolist(),columns = ['Subject','Keyword'])
    df2 = pd.DataFrame(df1.Keyword.str.split('(',1).tolist(),columns = ['Keyword', 'Count'])
    df3 = pd.concat([df1['Subject'],df2['Keyword'], df2['Count']], axis =1) 
    df3['Count'] = df3['Count'].apply(lambda x: x.rstrip(")"))
    
    base = os.path.basename(file)
    filename = os.path.splitext(base)[0]
    #data_resume= ResumeParser(file).get_extracted_data() 
    name = filename.split('_')
    name2 = name[0]
    name2 = name2.lower()
    ## converting str to dataframe
    name3 = pd.read_csv(StringIO(name2),names = ['Candidate Name'])
    #email_candidate= [data_resume['email']]
    #mobile_number_candidate= [data_resume['mobile_number']]
    #designations_candidate= [data_resume['designation']]
    #prev_companies_candidate= [data_resume['company_names']]
    #experience_candidate= [data_resume['total_experience']]
    
    
    dataf = pd.concat([name3['Candidate Name'], df3['Subject'], df3['Keyword'], df3['Count']], axis = 1)
    dataf['Candidate Name'].fillna(dataf['Candidate Name'].iloc[0], inplace = True)
    #data_add= pd.DataFrame({'Candidate Name': name2, 'Email_ID':email_candidate,'Mobile_Number':mobile_number_candidate,'Previous Designations':designations_candidate,'Previous Companies':prev_companies_candidate})
    dataf['File Name']= file
    return(dataf)

########
file_format= '.pdf'
st.markdown("<h1 style='text-align: center; color: blue;'>Solutions.AI Resume Screener</h1>", unsafe_allow_html=True)



uploaded_file = st.file_uploader("Please Upload a Zip file Containing Resume", type="zip")
if (uploaded_file is not None):
    zf = zipfile.ZipFile(uploaded_file)
    onlyfiles=zf.namelist()
    final_database=pd.DataFrame()
    final_database_add=pd.DataFrame()
    i = 0 
    while i < len(onlyfiles):
        file = onlyfiles[i]
        dat = create_profile(file)
        final_database = final_database.append(dat)
        i +=1
        print(i)
    final_database2 = final_database['Keyword'].groupby([final_database['File Name'],final_database['Candidate Name'], final_database['Subject']]).count().unstack()
    final_database2.reset_index(inplace = True)
    final_database2.fillna(0,inplace=True)
    final_database2['Total Score']= final_database2.sum(axis=1)
    final_database2= final_database2.sort_values(by='Total Score', ascending=False)
    column_list= final_database2.columns[1:]
    final_database3= pd.melt(final_database2, id_vars=['Candidate Name'], value_vars=final_database2.columns[2:-1])
    final_database3= final_database3.rename(columns= {'value':'Score'})
    final_database4= final_database2.sort_values(by="Total Score", ascending=False).head()
    final_database5=pd.melt(final_database4, id_vars=['Candidate Name'], value_vars=final_database4.columns[2:-1])
    final_database5= final_database5.rename(columns= {'value':'Score'})
    final_database5= final_database5.merge(final_database4[['Candidate Name','Total Score']], how='left', on='Candidate Name')
    fig= px.bar(final_database5.sort_values(by='Total Score', ascending=True), x='Score', y= 'Candidate Name', orientation='h',color='Subject', title="Top 5 Candidates vs Total Score")
    st.plotly_chart(fig)
    sub_list=final_database3.Subject.unique()
    for i in range(0,len(sub_list)):
        final_database_test_1= final_database3[final_database3.Subject==sub_list[i]]
        final_database_test_2= final_database_test_1.sort_values(by='Score', ascending=False).head()
        final_database_test_2= final_database_test_2[final_database_test_2['Score']>0]
        title_name= "Top 5 Candidate vs "+ sub_list[i]
        fig= px.bar(final_database_test_2.sort_values(by='Score', ascending=True), x='Score', y= 'Candidate Name', orientation='h', title=title_name)
        st.plotly_chart(fig)
    csv = final_database2.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings
    linko= f'<a href="data:file/csv;base64,{b64}" download="myfilename.csv">Download Candidate Score File(.csv)</a>'
    st.markdown(linko, unsafe_allow_html=True)
else:
    st.error("Please Upload a Zip File(.zip) containing Resume")

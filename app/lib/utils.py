from datetime import datetime
import requests, os, re, json, time
import pandas as pd
from sqlalchemy import create_engine
from os import listdir
from os.path import isfile, join
from tqdm import tqdm

def read_episoden_to_json(show_name):
    f = open("out/"+show_name+"/episoden.json",encoding='utf-8')
    j = json.load(f)
    f.close()
        
    return j

def read_html_to_json(show_name):
    fp = 'out/'+ show_name + "/html"
    l_fp = [fp + "/" + f for f in listdir(fp) if isfile(join(fp, f))]
    j_html = {}
    for fp in tqdm(l_fp):
        n = fp.split(".")
        n=n[0].split("/")
        n=str(n[-1])
        f = open(fp,"r",encoding='utf-8')
        html = f.read()
        f.close()
        j_html[n] = html
    
    return j_html


def dummy():
    return 23

def write_file(s, fp, fn, write_mode = "w"):
    if not os.path.isdir(fp):
        os.makedirs(fp)

    f = open(fp +"/"+fn, write_mode,encoding='utf-8')
    f.write(s)
    f.close()

    return 1

def download_links(show_name):

    links = []
    url = "https://www.fernsehserien.de/"+show_name+"/episodenguide/"
    response = requests.get(url)
    t = response.text   

    str1 = 'href="/'+show_name+'/folgen'
    i1 = t.find(str1)
    while i1>-1:
        i2 = t.find('"', i1+len(str1))
        links.append(t[i1:i2])
        i1 = t.find('href="/'+show_name+'/folgen', i2)

    links = list(set(links))
    links = ["https://www.fernsehserien.de/" + e.replace('href="',"") for e in links]

    write_file("\n".join(links), 'out/'+show_name, "links.txt")

    return links

def download_links_old(show_name):

    links = []

    ct = 0
    while True:
        ct = ct + 1
        url = "https://www.fernsehserien.de/"+show_name+"/sendetermine"
        if ct >1:
            url = url + "/-" + str(ct)
        if ct > 30:
            break
        
        print(url)
        cct = 0

        try:
            response = requests.get(url)
        except:
            print("LINK ERROR")
            break

        t = response.text   

        str1 = 'href="/'+show_name+'/folgen'
        i1 = t.find(str1)
        while i1>-1:
            i2 = t.find('"', i1+len(str1))
            links.append(t[i1:i2])
            i1 = t.find('href="/'+show_name+'/folgen', i2)

    links = list(set(links))
    links = ["https://www.fernsehserien.de/" + e.replace('href="',"") for e in links]

    write_file("\n".join(links), 'out/'+show_name, "links.txt")

    return links

def download_html_from_links(show_name, links, skip_available_files = True):

    j_html = {}

    if skip_available_files:
        fp = "out/"+show_name+"/html"
        available_files = [e.split('.', 1)[0] for e in os.listdir(fp)]

    for url in links:
        
        

        n = url.split("/")
        n = n[-1].split("-")
        n = n[0]

        if skip_available_files and n in available_files:
            print("skip")
            continue

        try:
            response = requests.get(url)
        except:
            print("Error on url " + url)
            time.sleep(61)
            response = requests.get(url)
            print("Error solved for url " + url)
        t = response.text

        write_file(t, 'out/'+show_name + "/html", n +".html")
        j_html[n] = t

    return j_html



def extract_json_from_html(show_name, j_html):

    fp_episoden = 'out/'+show_name+'/episoden'
    if not os.path.isdir(fp_episoden):
        os.makedirs(fp_episoden)


    episoden = {}

    ct = 0
    for n in tqdm(j_html):
        t = j_html[n]
        ct = ct + 1
        episoden_dummy = {}

        # finde personen
        gaeste = []
        str1 = '<dt itemprop="name">'
        i1 = t.find(str1)
        while i1 >-1:
            gaeste_dummy = {}
            i1 = i1 + len(str1)
            i2 = t.find("</p>", i1)
            dummy = t[i1:i2].replace("<dd>","").replace("<p>","").replace("</dd>","").split("</dt>")
            gaeste_dummy["name"] = dummy[0]
            beschreibung = dummy[1]
            try:
                dummy = "(" + re.search('\(([^)]+)', name).group(1) + ")"
                name = name.replace(dummy,"")
                name = name.strip()
                beschreibung = dummy + " " + beschreibung
            except:
                dummy = ""

            gaeste_dummy["beschreibung"] = beschreibung
            gaeste.append(gaeste_dummy)
            i1 = t.find(str1, i2)


        # finde beschreibung
        str_start = '<div class="episode-output-inhalt-inner">'
        str_end = '</div>'
        i1 = t.find(str_start) + len(str_start)
        i2 = t.find(str_end, i1)
        s = 1
        while s > 0:
            n_open_divs = (len(t[i1:i2])-len(t[i1:i2].replace("<div","")))/4
            n_close_divs = (len(t[i1:i2])-len(t[i1:i2].replace("</div>","")))/6
            s = n_open_divs-n_close_divs
            i2 = t.find(str_end, i2+1)

        # both needed
        content = re.sub('<span.*?</span>','',t[i1:i2-7], flags=re.DOTALL)
        content = re.sub('<.*?>','',content, flags=re.DOTALL)



        i1 = t.find("<ea-angabe-datum>")
        i2 = t.find("</ea-angabe-datum>")
        datum_episode = t[i1+20:i2]
            

        episoden_dummy["thema"] = content
        episoden_dummy["gaeste"] = gaeste
        episoden_dummy["datum"] = datum_episode
        episoden_dummy["sendung"] = show_name
        episoden[str(n) + "__" + show_name] = episoden_dummy.copy()
        



    with open("out/"+show_name + "/" + "episoden.json", "w", encoding='utf-8') as outfile:
        json.dump(episoden, outfile, indent=4, ensure_ascii=False)

    return episoden



def episoden_to_df(episoden):
    l = []
    for e in episoden:
        for g in episoden[e]["gaeste"]:
            nachname = g["name"].split(" ")
            vorname = nachname[0]
            nachname = nachname[-1]
            g["nachname"] = nachname
            g["vorname"] = vorname
            g["thema"] = episoden[e]["thema"]
            g["datum"] = datetime.strptime(episoden[e]["datum"], '%d.%m.%Y')
            g["nummer"] = e

    for e in episoden:
        for g in episoden[e]["gaeste"]:
            l.append(g)

    return pd.DataFrame.from_records(l)
    

def write_df_to_db(table_name, df, constr):
    e = create_engine("sqlite:///" + constr)
    df.to_sql(table_name, e, if_exists='replace', index = True)

    return 1

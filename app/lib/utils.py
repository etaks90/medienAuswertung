import matplotlib.pyplot as plt
from datetime import datetime
import requests, os, re, json, time
import pandas as pd
from sqlalchemy import create_engine
from os import listdir
from os.path import isfile, join
from tqdm import tqdm

def read_episoden_to_json(show_name, local_folder):
    f = open(local_folder+show_name+"/episoden.json",encoding='utf-8')
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


def plot_time_evolution(df_episoden, df_gaeste, filter_sendung):

    d = {}
    for y in range(2010,2024):
        start_date = datetime(y, 1, 1)
        end_date = datetime(y+1, 12, 31)

        df = df_episoden.merge(df_gaeste, how = "left", on = ["name"])
        mask = (df['datum'] > start_date) & (df['datum'] <= end_date)
        if not(filter_sendung.lower() == "alle"):
            df = df[df["sendung"] == filter_sendung]
        df = df.sort_values(by=['datum'], ascending=True)
        df = df.loc[mask]
        if len(df) == 0:
            print(y)
            continue

        df_dummy = df[df["partei"].str.len()>0]
        parteien = list(set(df_dummy["partei"].to_list()))
        c = []
        for partei in parteien:
            c.append(100 * len(df[df["partei"] == partei])/len(df_dummy))

        
        labels = parteien
        c = [100*e/sum(c) for e in c]

        for partei, partei_count in zip(labels, c):
            if not partei in d:
                d[partei] = {}
                d[partei]["t"] = []
                d[partei]["c"] = []
            d[partei]["t"].append(y)
            d[partei]["c"].append(partei_count)


    # https://matplotlib.org/stable/gallery/color/named_colors.html
    color_vec = {}
    color_vec["SPD"] = "r"
    color_vec["Grüne"] = "g"
    color_vec["FDP"] = "y"
    color_vec["CDU"] = "k"
    color_vec["CSU"] = "cyan"
    color_vec["AFD"] = "b"
    color_vec["Linke"] = "m"
    fig = plt.figure()
    for k, v in d.items():
        if k.count(",")>0:
            continue
        if k in color_vec:
            c = color_vec[k]
        else:
            c = "k"
        plt.plot(v["t"], v["c"], label = k, c = c, linewidth = 3)

    plt.legend(loc="upper center", ncol=3)
    #figure(figsize=(8, 6), dpi=800)
    ax = plt.gca()
    ax.set_xlim([2009, 2023])
    ax.set_ylim([-1, 35])
    fig.suptitle('Prozentualer Anteil eingeschränkt auf ' + filter_sendung, fontsize=20)
    plt.xlabel('Jahr', fontsize=18)
    plt.ylabel('%', fontsize=16)
    plt.savefig('out/plots/zeitentwicklung__'+filter_sendung+'.pdf', bbox_inches = "tight")
    plt.figure().clear()
    plt.close()
    plt.cla()
    plt.clf()

def prepare_df_for_eval_zeitentwicklung(l_show_name):
    local_folder = r"C:\Users\oliver.koehn\Documents\talkshowsAuswerten\app\out\\"

    episoden = []
    for show_name in l_show_name:
        
        episoden.append(read_episoden_to_json(show_name, local_folder))

    episoden = {k:v for element in episoden for k,v in element.items()}
    df_episoden = episoden_to_df(episoden)
    df_episoden["sendung"] = df_episoden["nummer"].str.split("__").str[-1]


    j_gaeste = {}
    liste_parteien = ["SPD", "Grüne", "FDP", "CDU", "CSU", "AFD", "Linke"]

    for e in episoden:
        for g in episoden[e]["gaeste"]:
            if not(g["name"] in j_gaeste):
                j_gaeste[g["name"]] = {}
                j_gaeste[g["name"]]["beschreibung"] = []
                j_gaeste[g["name"]]["partei"] = []
            j_gaeste[g["name"]]["beschreibung"].append(g["beschreibung"])
            j_gaeste[g["name"]]["beschreibung"] = list(set(j_gaeste[g["name"]]["beschreibung"]))
            partei = []
            for partei in liste_parteien:
                if partei.lower() in g["beschreibung"].lower():
                    j_gaeste[g["name"]]["partei"].append(partei)
                    j_gaeste[g["name"]]["partei"] = list(set(j_gaeste[g["name"]]["partei"]))

    l = []
    for e in j_gaeste:
        j_dummy = {}
        j_dummy["name"] = e
        j_dummy["beschreibung"] = ",".join(j_gaeste[e]["beschreibung"])
        j_dummy["partei"] = ",".join(j_gaeste[e]["partei"])
        l.append(j_dummy.copy())

    df_gaeste = pd.DataFrame.from_records(l)

    return df_episoden, df_gaeste
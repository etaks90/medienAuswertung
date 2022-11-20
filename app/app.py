from lib import utils
import json
import pandas as pd

l_show_name= ["anne-will", "hart-aber-fair", "maischberger-ard", "markus-lanz", "maybrit-illner"]

local_folder = r"C:\Users\oliver.koehn\Documents\talkshowsAuswerten\app\out\\"

episoden = []
for show_name in l_show_name:
    
    episoden.append(utils.read_episoden_to_json(show_name, local_folder))

episoden = {k:v for element in episoden for k,v in element.items()}
df = utils.episoden_to_df(episoden)
utils.write_df_to_db("SENDUNGEN", df, constr = r"C:\Users\oliver.koehn\Documents\talkshowsAuswerten\private\database\medien.db")


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
utils.write_df_to_db("Gaeste", pd.DataFrame.from_records(l), constr = r"C:\Users\oliver.koehn\Documents\talkshowsAuswerten\private\database\medien.db")
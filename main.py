import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path
import plotly.graph_objects as go
from shapely.geometry import Polygon, LineString, Point
import plotly.graph_objects as go
import webbrowser
import os

global tabella_componenti

moltiplicatore_sporto = 3


import pandas as pd

tabella_componenti = pd.DataFrame(columns=[
    "n", "nome", "tag", "lunghezza", "larghezza", "altezza", "volume_m3", "costo_euro"
])




def chiedi_dati_preventivo():
    print("\n📋 Inserisci i dati del preventivo")

    def obbligatorio(prompt):
        while True:
            v = input(prompt).strip()
            if v:
                return v
            print("⚠️ Campo obbligatorio, riprova.")

    def numero_libero(prompt):
        # accetta telefono o numero di riferimento (cifre, +, spazi, -, /, (), #)
        while True:
            v = input(prompt).strip()
            if not v:
                print("⚠️ Campo obbligatorio, riprova.")
                continue
            # deve contenere almeno una cifra
            if any(ch.isdigit() for ch in v):
                return v
            print("⚠️ Inserisci almeno una cifra (telefono o numero di riferimento).")

    dati = {
        "Nome Cliente": obbligatorio("Nome cliente: "),
        "Progetto": obbligatorio("Nome progetto: "),
        "Numero": numero_libero("Numero (telefono o riferimento): "),
        "Cantiere": obbligatorio("Cantiere: "),

    }
    return dati



def aggiungi_componenti(tag, nome, lista_componenti, allungamento=0.0):
    global tabella_componenti
    n_base = len(tabella_componenti) + 1

    righe = []
    for i, (tipo, posizione, lunghezza) in enumerate(lista_componenti, 1):
        lunghezza_tot = lunghezza + allungamento

        righe.append({
            "n": n_base + i - 1,
            "nome": nome,
            "tag": tag,  # es. "Correntino", "Colmo", "Displuvio"
            "lunghezza": round(lunghezza_tot, 3),
            "larghezza": None,
            "altezza": None,
            "volume_m3": None,
            "costo_euro": None
        })

    tabella_componenti = pd.concat([tabella_componenti, pd.DataFrame(righe)], ignore_index=True)


def completa_tabella_componenti(tabella_componenti):
    import pandas as pd

    sezioni = {}
    tag_unici = tabella_componenti["tag"].unique()

    # Chiedi sezione per ogni tag (in cm) e converti in metri
    for tag in tag_unici:
        print(f"\n🔧 Imposta sezione per il componente: {tag}")
        while True:
            try:
                larghezza_cm = float(input(f"Inserisci larghezza in cm per {tag}: "))
                altezza_cm = float(input(f"Inserisci altezza in cm per {tag}: "))
                larghezza = larghezza_cm / 100
                altezza = altezza_cm / 100
                sezioni[tag] = (larghezza, altezza)
                break
            except ValueError:
                print("❌ Inserisci un numero valido.")

    # Costo al metro cubo
    while True:
        try:
            costo_m3 = float(input("\n💰 Inserisci il costo al metro cubo (€): "))
            break
        except ValueError:
            print("❌ Inserisci un valore numerico valido.")

    # Aggiorna la tabella
    for i, row in tabella_componenti.iterrows():
        tag = row["tag"]
        lunghezza = row["lunghezza"]
        larg, alt = sezioni[tag]
        volume = larg * alt * lunghezza
        costo = volume * costo_m3

        tabella_componenti.at[i, "larghezza"] = larg
        tabella_componenti.at[i, "altezza"] = alt
        tabella_componenti.at[i, "volume_m3"] = volume
        tabella_componenti.at[i, "costo_euro"] = costo

    # Totale
    costo_totale = tabella_componenti["costo_euro"].sum()
    # Aggiungi riga finale con il totale
    tabella_componenti.loc[len(tabella_componenti)] = [""] * len(tabella_componenti.columns)
    tabella_componenti.loc[len(tabella_componenti)] = [
        "", "TOTALE", "", "", "", "", "", costo_totale
    ]
    print(f"\n💸 Costo totale dei componenti: € {costo_totale:,.2f}")

    return tabella_componenti




from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image as PILImage  # attenzione: nomi diversi
import os
import datetime


def genera_report_completo(nome_file_pdf, tabella_componenti, path_logo="logo.png", path_disegno="disegno2d.png", dati_preventivo=None):
    doc = SimpleDocTemplate(nome_file_pdf, pagesize=A4)
    elementi = []
    styles = getSampleStyleSheet()

    # 1️⃣ Logo
    if os.path.exists(path_logo):
        # Carica l'immagine con Pillow
        img_pil = PILImage.open(path_logo)
        width, height = img_pil.size

        # Larghezza target in punti (es. 150 pt), altezza calcolata proporzionalmente
        width_pt = 250
        ratio = height / width
        height_pt = width_pt * ratio

        logo = Image(path_logo, width=width_pt, height=height_pt)
        logo.hAlign = 'CENTER'
        elementi.append(logo)
    else:
        elementi.append(Paragraph("[Logo non trovato]", styles['Normal']))

    elementi.append(Spacer(1, 12))



    # 2️⃣ Intestazione e data
    elementi.append(Paragraph("<b>Preventivo Tetto</b>", styles['Title']))
    data_attuale = datetime.datetime.now().strftime("%d/%m/%Y")
    elementi.append(Paragraph(f"Data: {data_attuale}", styles['Normal']))
    elementi.append(Spacer(1, 24))

    # 3️⃣ Dati preventivo
    if dati_preventivo:
        elementi.append(Paragraph("<b>Dati preventivo:</b>", styles['Heading3']))
        for chiave, valore in dati_preventivo.items():
            elementi.append(Paragraph(f"{chiave}: {valore}", styles['Normal']))
        elementi.append(Spacer(1, 16))

    # 4️⃣ Disegno 2D
    if os.path.exists(path_disegno):
        elementi.append(Paragraph("Vista 2D del tetto", styles['Heading3']))
        img = Image(path_disegno, width=400, height=300)
        img.hAlign = 'CENTER'
        elementi.append(img)
        elementi.append(Spacer(1, 24))
    else:
        elementi.append(Paragraph("[Disegno 2D non trovato]", styles['Normal']))
        elementi.append(Spacer(1, 16))

    # 5️⃣ Tabella componenti
    colonne = list(tabella_componenti.columns)
    dati = [colonne] + tabella_componenti.values.tolist()

    tabella = Table(dati, repeatRows=1)
    tabella.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ]))
    elementi.append(Paragraph("Tabella componenti", styles['Heading3']))
    elementi.append(Spacer(1, 12))
    elementi.append(tabella)

    # ✅ Generazione PDF
    doc.build(elementi)
    return f"✅ PDF generato con successo: {nome_file_pdf}"



def capriata(
    larghezza_casa,
    correntino_dx,
    correntino_sx,
    altezza_colmo,
    pendenza_dx,
    pendenza_sx,
    nome="Capriata"
):
    """
    Calcola gli elementi principali della capriata e li moltiplica per il numero di capriate,
    richiesto all’utente via input.
    """

    # Chiedi numero capriate
    while True:
        try:
            n_capriate = int(input(f"\nQuante capriate identiche '{nome}' vuoi calcolare? "))
            if n_capriate < 1:
                print("❌ Inserisci un numero positivo.")
                continue
            break
        except ValueError:
            print("❌ Inserisci un numero intero valido.")

    monaco = altezza_colmo - 0.20  # lunghezza effettiva

    # Saette
    saetta_destra = monaco / math.sin(math.radians(pendenza_sx)) if pendenza_sx != 0 else 0
    saetta_sinistra = monaco / math.sin(math.radians(pendenza_dx)) if pendenza_dx != 0 else 0


    # Output per ogni singola capriata
    for i in range(1, n_capriate + 1):
        print(f"\n🔺 {nome} {i}")
        print(f"📏 Puntone destro: {correntino_dx:.2f} m")
        print(f"📏 Puntone sinistro: {correntino_sx:.2f} m")
        print(f"📐 Catena (base): {larghezza_casa:.2f} m")
        print(f"↕️ Monaco (verticale): {monaco:.2f} m")
        print(f"📏 Saetta destra (↙ pendenza sx): {saetta_destra:.2f} m")
        print(f"📏 Saetta sinistra (↘ pendenza dx): {saetta_sinistra:.2f} m")

    elementi = []

    for i in range(n_capriate):
        elementi.extend([
            ("Puntone", 0, correntino_dx),
            ("Puntone", 0, correntino_sx),
            ("Catena", 0, larghezza_casa),
            ("Monaco", 0, monaco),
            ("Saetta", 0, saetta_destra),
            ("Saetta", 0, saetta_sinistra)
        ])



    return elementi






def calcola_perimetro_rettangolare(lato_lungo, lato_corto):
    return 2 * (lato_lungo + lato_corto)

def calcola_perimetro_L(lunghezza_A, larghezza_A, lunghezza_B, larghezza_B):
    blocco_1 = lunghezza_A + larghezza_A + lunghezza_A + larghezza_B
    blocco_2 = lunghezza_B + larghezza_B + lunghezza_B +larghezza_A
    return blocco_1 + blocco_2

def stampa_correntini(nome_falda, correntini, allungamento):
    print(f"\n--- Correntini {nome_falda.upper()} ---")
    print(f"[Allungamento per sporto: {allungamento:.2f} m]")

    for _, posizione, lunghezza_base in correntini:
        lunghezza_totale = lunghezza_base + allungamento
        direzione = (
            "colmo"
            if posizione == 0
            else f"{abs(posizione):.2f} m {'→ destra' if posizione > 0 else '← sinistra'}"
        )
        print(
            f"Posizione: {direzione} | Base: {lunghezza_base:.2f} m + Allungamento: {allungamento:.2f} m → Totale: {lunghezza_totale:.2f} m"
        )





def calcola_allungamento_correntino(sporto, pendenza_gradi):
    if sporto == 0:
        return 0.0
    angolo_rad = math.radians(pendenza_gradi)
    return 1 * (sporto / math.cos(angolo_rad))




def stampa_correntini(nome_falda, correntini, allungamento):
    print(f"\n--- Correntini {nome_falda.upper()} ---")
    for _, posizione, lunghezza_base in correntini:
        lunghezza_totale = lunghezza_base + allungamento
        direzione = (
            "colmo"
            if posizione == 0
            else f"{abs(posizione):.2f} m {'→ destra' if posizione > 0 else '← sinistra'}"
        )
        print(f"Posizione: {direzione} | allungamento: {allungamento:.2f} m | Base: {lunghezza_base:.2f} m → Totale: {lunghezza_totale:.2f} m")



def visualizza_tetto_L_3d_completo(
    h_colmo,
    spostamento_colmo_A,
    spostamento_colmo_B,
    lar_A, lar_B, lun_A, lun_B,
    taglio_A, taglio_B,
    interasse_triangolari, interasse_trapezoidali,
):
    x0, y0 = 0, 0

    nodo_colmo = (
        x0 + lar_A / 2 + spostamento_colmo_A,
        y0 + lar_B / 2 + spostamento_colmo_B,
        h_colmo
    )

    # Ricostruzione 2D dei punti di colmi e compluvi
    colmo_A_top = (nodo_colmo[0], y0 + lar_B + lun_A - taglio_A)
    colmo_B_right = (x0 + lar_A + lun_B - taglio_B, nodo_colmo[1])
    angolo_interno = (x0 + lar_A, y0 + lar_B)

    displuvi = [
        ((x0, y0 + lar_B + lun_A), colmo_A_top),
        ((x0 + lar_A, y0 + lar_B + lun_A), colmo_A_top),
        ((x0 + lar_A + lun_B, y0), colmo_B_right),
        ((x0 + lar_A + lun_B, y0 + lar_B), colmo_B_right),
        ((x0, y0), (nodo_colmo[0], nodo_colmo[1])),

    ]

    # Falda triangolare A (sx)
    falda_tri_A = [
        (x0, y0 + lar_B + lun_A, 0),
        (nodo_colmo[0], y0 + lar_B + lun_A - taglio_A, h_colmo),
        (x0 + lar_A, y0 + lar_B + lun_A, 0)
    ]

    # Falda triangolare B (dx)
    falda_tri_B = [
        (x0 + lar_A + lun_B, y0 + lar_B, 0),
        (x0 + lar_A + lun_B - taglio_B, y0 + lar_B / 2 + spostamento_colmo_B, h_colmo),
        (x0 + lar_A + lun_B, y0, 0)
    ]

    # Falda trapezoidale A (verticale)
    falda_trap_A = [
        (x0, y0, 0),
        (nodo_colmo[0], nodo_colmo[1], h_colmo),
        (nodo_colmo[0], y0 + lar_B + lun_A - taglio_A, h_colmo),
        (x0, y0 + lun_A + lar_B, 0)
    ]

    # Falda trapezoidale B (orizzontale)
    falda_trap_B = [
        (x0, y0, 0),
        (x0 + lar_A + lun_B, y0, 0),
        (x0 + lar_A + lun_B - taglio_B, nodo_colmo[1], h_colmo),
        (nodo_colmo[0], nodo_colmo[1], h_colmo)
    ]

    # Falda parallelepipedo C (sotto)
    falda_parall_C = [
        (nodo_colmo[0], nodo_colmo[1], h_colmo),
        (x0 + lar_A, y0 + lar_B, 0),
        (x0 + lar_A, y0 + lar_B + lun_A, 0),
        (nodo_colmo[0], y0 + lar_B + lun_A - taglio_A, h_colmo)
    ]

    # Falda parallelepipedo D (sopra)
    falda_parall_D = [
        (nodo_colmo[0], nodo_colmo[1], h_colmo),
        (x0 + lar_A + lun_B - taglio_B, nodo_colmo[1], h_colmo),
        (x0 + lar_A + lun_B, y0 + lar_B, 0),
        (x0 + lar_A, y0 + lar_B, 0)
    ]

    fig = go.Figure()

    falde = [
        (falda_tri_A, interasse_triangolari, 'verticale'),
        (falda_tri_B, interasse_triangolari, 'orizzontale'),
        (falda_trap_A, interasse_trapezoidali, 'orizzontale'),
        (falda_trap_B, interasse_trapezoidali, 'verticale'),
        (falda_parall_C, interasse_trapezoidali, 'orizzontale'),
        (falda_parall_D, interasse_trapezoidali, 'verticale'),
    ]

    for falda, interasse, orient in falde:
        riempi_falda_con_linee_3d(fig, falda, orientamento=orient, interasse=interasse)
        x, y, z = zip(*falda)
        fig.add_trace(go.Mesh3d(
            x=x, y=y, z=z,
            opacity=1,
            color='lightgray',
            showlegend=False
        ))

    # Nodo colmo centrale
    fig.add_trace(go.Scatter3d(
        x=[nodo_colmo[0]],
        y=[nodo_colmo[1]],
        z=[nodo_colmo[2]],
        mode='markers',
        marker=dict(size=5, color='red'),
        name='Nodo colmo'
    ))

    # Colmi e compluvi
    fig.add_trace(go.Scatter3d(
        x=[colmo_A_top[0], nodo_colmo[0]],
        y=[colmo_A_top[1], nodo_colmo[1]],
        z=[h_colmo, h_colmo],
        mode='lines',
        line=dict(color='red', width=4),
        name='Colmo A'
    ))

    fig.add_trace(go.Scatter3d(
        x=[colmo_B_right[0], nodo_colmo[0]],
        y=[colmo_B_right[1], nodo_colmo[1]],
        z=[h_colmo, h_colmo],
        mode='lines',
        line=dict(color='red', width=4),
        name='Colmo B'
    ))



    for i, (p2d, colmo2d) in enumerate(displuvi):
        fig.add_trace(go.Scatter3d(
            x=[p2d[0], colmo2d[0]],
            y=[p2d[1], colmo2d[1]],
            z=[0, h_colmo],
            mode='lines',
            line=dict(color='blue', width=3),
            name=f'Displuvio {i+1}'
        ))


    fig.add_trace(go.Scatter3d(
        x=[nodo_colmo[0], angolo_interno[0]],
        y=[nodo_colmo[1], angolo_interno[1]],
        z=[h_colmo, 0],
        mode='lines',
        line=dict(color='green', width=4),
        name='Compluvio'
    ))


    fig.update_layout(
        scene=dict(
            xaxis=dict(title='X', backgroundcolor='white', gridcolor='lightgray'),
            yaxis=dict(title='Y', backgroundcolor='white', gridcolor='lightgray'),
            zaxis=dict(title='Z', backgroundcolor='white', gridcolor='lightgray'),
            aspectmode='data'
        ),
        title="Tetto a L 3D - Architettonico",
        showlegend=True
    )

    output_path = "tetto_L_3D.html"
    fig.write_html(output_path)
    print(f"✅ Visualizzazione salvata in '{output_path}'")
    #webbrowser.open("file://" + os.path.abspath(output_path))











def calcola_colmo_trapezoidale(titolo, lunghezza_blocco, base_sx, base_dx):
    lunghezza_colmo = lunghezza_blocco - (base_sx + base_dx)
    print(f"📏 Lunghezza colmo {titolo}: {lunghezza_colmo:.2f} m  (Blocchi: {lunghezza_blocco} - Basi: {base_sx} + {base_dx})")
    return lunghezza_colmo



def calcola_correntini_falda_triangolare_L(nome_falda, base_sx, base_dx, altezza_colmo, interasse, taglio):
    print(f"\n--- Correntini per la falda {nome_falda.upper()} (triangolare, colmo decentrato) ---")

    correntini = []

    # Correntino principale (al colmo)
    lunghezza_colmo = math.sqrt(taglio ** 2 + altezza_colmo ** 2)
    correntini.append(("colmo", 0.0, lunghezza_colmo))
    print(f"Pos 0.00 m (colmo) | Lunghezza: {lunghezza_colmo:.2f} m")

    # Calcolo rapporti corretti
    rapporto_dx = lunghezza_colmo / base_dx
    rapporto_sx = lunghezza_colmo / base_sx

    # Lato destro
    print("\n[Triangolo lato destro]")
    distanza = 0.0
    while True:
        distanza += interasse
        nuova_base = base_dx - distanza
        if nuova_base <= 0:
            break
        lunghezza = nuova_base * rapporto_dx
        correntini.append(("triangolo_dx", distanza, lunghezza))
        print(f"Pos {distanza:.2f} m | Lunghezza: {lunghezza:.2f} m")

    # Lato sinistro
    print("\n[Triangolo lato sinistro]")
    distanza = 0.0
    while True:
        distanza += interasse
        nuova_base = base_sx - distanza
        if nuova_base <= 0:
            break
        lunghezza = nuova_base * rapporto_sx
        correntini.append(("triangolo_sx", -distanza, lunghezza))
        print(f"Pos -{distanza:.2f} m | Lunghezza: {lunghezza:.2f} m")

    return correntini








def calcola_lunghezze_tetto_L(colmo_A_top, nodo_colmo, colmo_B_right, angolo_interno, displuvi, altezza_colmo):
    import math

    def distanza_3d(p1, p2, z1=0, z2=0):
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (z2 - z1)**2)

    lung_colmo_A = distanza_3d(colmo_A_top, nodo_colmo, altezza_colmo, altezza_colmo)
    lung_colmo_B = distanza_3d(colmo_B_right, nodo_colmo, altezza_colmo, altezza_colmo)
    lung_compluvio = distanza_3d(nodo_colmo, angolo_interno, altezza_colmo, 0)

    punti_alti = {colmo_A_top, colmo_B_right, nodo_colmo}

    displuvi_lunghezze = []
    for p1, p2 in displuvi:
        z1 = altezza_colmo if p1 in punti_alti else 0
        z2 = altezza_colmo if p2 in punti_alti else 0
        displuvi_lunghezze.append(distanza_3d(p1, p2, z1, z2))


    print("\n--- LUNGHEZZE (3D) ---")
    print(f"Colmo A (verticale): {lung_colmo_A:.6f} m")
    print(f"Colmo B (orizzontale): {lung_colmo_B:.6f} m")
    print(f"Compluvio: {lung_compluvio:.6f} m")
    print("Displuvi:")
    print(f"  - A sinistra: {displuvi_lunghezze[0]:.6f} m")
    print(f"  - A destra: {displuvi_lunghezze[1]:.6f} m")
    print(f"  - B basso: {displuvi_lunghezze[2]:.6f} m")
    print(f"  - B alto: {displuvi_lunghezze[3]:.6f} m")
    print(f"  - Centrale: {displuvi_lunghezze[4]:.6f} m")
    print("✅ Calcolo delle lunghezze 3D completato.")

    return lung_colmo_A, lung_colmo_B, lung_compluvio, displuvi_lunghezze


def gestisci_tetto_L(usa_tamponatura=False):
    print("\n--- CONFIGURAZIONE TETTO A L ---")

    print("\n--- Dimensioni blocchi ---")
    lunghezza_A = float(input("Lunghezza blocco A (m): "))  # verticale
    larghezza_A = float(input("Larghezza blocco A (m): "))
    lunghezza_B = float(input("Lunghezza blocco B (m): "))  # orizzontale
    larghezza_B = float(input("Larghezza blocco B (m): "))

    lato_lungo_A = max(lunghezza_A, larghezza_A)
    lato_lungo_B = max(lunghezza_B, larghezza_B)

    lato_lungo = max(lato_lungo_A, lato_lungo_B)
    lato_corto = min(lato_lungo_A, lato_lungo_B)

    print("\n--- CONFIGURAZIONE SPORTO ---")
    sporto = float(input("Inserisci lo sporto desiderato (in metri): "))

    print("\nTipo di sporto:")
    print("1 - Classico (estensione del correntino)")
    print("2 - Passafuori (non ancora implementato)")
    tipo_sporto = input("Seleziona il tipo di sporto (1 o 2): ").strip()


    print("\n--- Pendenze falde ---")
    pendenza_tri_A = chiedi_pendenza("Falda triangolare A")
    pendenza_tri_B = chiedi_pendenza("Falda triangolare B")
    pendenza_trap = chiedi_pendenza("Falde trapezoidali (comuni)")
    pendenza_parall = chiedi_pendenza("Falde parallelepipedo (comuni)")

    # Calcolo altezza colmo (usando pendenza trapezoidale + parallelepipedo)
    h_trap = math.tan(math.radians(pendenza_trap)) * (larghezza_A / 2)
    h_parall = math.tan(math.radians(pendenza_parall)) * (larghezza_B / 2)
    altezza_colmo = (h_trap + h_parall) / 2

    # Tagli colmo per falde triangolari
    taglio_A = altezza_colmo / math.tan(math.radians(pendenza_tri_A))
    taglio_B = altezza_colmo / math.tan(math.radians(pendenza_tri_B))

    print(f"\nAltezza colmo stimata: {altezza_colmo:.10f} m")
    print(f"Taglio blocco A: {taglio_A:.2f} m")
    print(f"Taglio blocco B: {taglio_B:.2f} m")

    interasse_trapezoidali = suggerisci_interasse_ottimale(min(lunghezza_A, lunghezza_B))
    print(f"\n[Consiglio] Interasse per falde trapezoidali e parallelepipede: {interasse_trapezoidali:.2f} m")
    usa_default = input(
        "Vuoi usare questo interasse per le falde trapezoidali/parallelepipede? (S/n): ").strip().lower()
    if usa_default == "n":
        try:
            interasse_trapezoidali = float(input("Inserisci interasse personalizzato: "))
        except ValueError:
            print("Valore non valido. Uso quello consigliato.")

    usa_stesso = input("Vuoi usare lo stesso interasse anche per le falde triangolari? (S/n): ").strip().lower()
    if usa_stesso == "n":
        try:
            interasse_triangolari = float(input("Inserisci interasse per le falde triangolari: "))
        except ValueError:
            interasse_triangolari = interasse_trapezoidali
    else:
        interasse_triangolari = interasse_trapezoidali

    colmo_A_top, nodo_colmo, colmo_B_right, angolo_interno, displuvi, altezza_colmo, spostamento_colmo_A, spostamento_colmo_B = disegna_tetto_L_2d_completo(
        lunghezza_A, larghezza_A, lunghezza_B, larghezza_B,
        pendenza_tri_A, pendenza_tri_B,
        pendenza_trap, pendenza_parall, interasse_triangolari, interasse_trapezoidali,
    )

    lung_colmo_A, lung_colmo_B, lung_compluvio, displuvi_lunghezze = calcola_lunghezze_tetto_L(
        colmo_A_top,
        nodo_colmo,
        colmo_B_right,
        angolo_interno,
        displuvi,
        altezza_colmo
    )

    print("\n➡️ Calcolo correntini per falda triangolare A (blocco verticale)")
    base_sx_A = (larghezza_A / 2) + spostamento_colmo_A
    base_dx_A = (larghezza_A / 2) - spostamento_colmo_A
    print("\n➡️ Calcolo correntini per falda triangolare B (blocco orizzontale)")
    base_sx_B = (larghezza_B / 2) + spostamento_colmo_B
    base_dx_B = (larghezza_B / 2) - spostamento_colmo_B

    # Calcolo basi falde trapezoidali
    base_A_sx = taglio_A
    base_A_dx = (larghezza_B / 2) + spostamento_colmo_B
    base_B_dx = taglio_B
    base_B_sx = (larghezza_A / 2) + spostamento_colmo_A
    print("base destra A")
    print(base_A_dx)
    print("base sinistra A")
    print(base_A_sx)
    print("base destra B")
    print(base_B_dx)
    print("base sinistra B")
    print(base_B_sx)

    # Calcolo colmi effettivi
    lunghezza_colmo_A = calcola_colmo_trapezoidale("A", lunghezza_A, base_A_sx, base_A_dx)
    lunghezza_colmo_B = calcola_colmo_trapezoidale("B", lunghezza_B, base_B_sx, base_B_dx)

    correntini_A = calcola_correntini_falda_triangolare_L(
        nome_falda="A",
        base_sx=base_sx_A,
        base_dx=base_dx_A,
        altezza_colmo=altezza_colmo,
        interasse=interasse_triangolari,
        taglio=taglio_A
    )




    correntini_B = calcola_correntini_falda_triangolare_L(
        nome_falda="B",
        base_sx=base_sx_B,
        base_dx=base_dx_B,
        altezza_colmo=altezza_colmo,
        interasse=interasse_triangolari,
        taglio=taglio_B

    )

    # 🔷 Calcolo falde trapezoidali (A e B)

    # Falda A (verticale)
    base_sx_A = taglio_A
    base_dx_A = (larghezza_B / 2) - spostamento_colmo_B

    # Falda B (orizzontale)
    base_dx_B = taglio_B
    base_sx_B = (larghezza_A / 2) - spostamento_colmo_A

    print("\n➡️ Calcolo correntini per falda trapezoidale A (blocco verticale)")
    correntini_falda_A = calcola_correntini_falda_trapezoidale_L(
        "A", lunghezza_A, base_dx_A, base_sx_A, altezza_colmo,
        interasse_trapezoidali, taglio_dx=taglio_A, taglio_sx=taglio_A,   pendenza_trap=pendenza_trap, escludi_displuvio_est=True
    )

    print("\n➡️ Calcolo correntini per falda trapezoidale B (blocco orizzontale)")
    correntini_falda_B = calcola_correntini_falda_trapezoidale_L(
        "B", lunghezza_B, base_dx_B, base_sx_B, altezza_colmo,
        interasse_trapezoidali, taglio_dx=taglio_B, taglio_sx=taglio_B,   pendenza_trap=pendenza_trap, escludi_displuvio_est=True
    )

    # 👉 QUI AGGIUNGI QUESTO BLOCCO:

    print("spostamento colmo A")
    print(spostamento_colmo_A)
    print("spostamento colmo B")
    print(spostamento_colmo_B)
    print("lunghezza colmo A")
    print(lunghezza_colmo_A)
    print("lunghezza colmo B")
    print(lunghezza_colmo_B)
    print("taglio A")
    print(taglio_A)
    print("taglio B")
    print(taglio_B)
    # ▶️ Lunghezza della parte rettangolare delle falde parallelepipede
    lunghezza_rettangolo_C = lunghezza_colmo_A - ((larghezza_B/2) - spostamento_colmo_B)
    lunghezza_rettangolo_D = lunghezza_colmo_B - ((larghezza_A/2) - spostamento_colmo_A)

    # ▶️ Basi laterali
    base_sx_C = taglio_A  # triangolo sinistro della falda C
    base_dx_C = (larghezza_B/2) - spostamento_colmo_B  # triangolo destro della falda C

    base_sx_D = (larghezza_A/2) - spostamento_colmo_A  # triangolo sinistro della falda D
    base_dx_D = taglio_B  # triangolo destro della falda D

    # ▶️ Calcolo correntini per falde parallelepipede
    print("\n➡️ Calcolo correntini per falda parallelepipeda C (blocco verticale)")
    correntini_falda_C = calcola_correntini_falda_parallelepipedale_L(
        nome_falda="C",
        lunghezza_rettangolo=lunghezza_rettangolo_C,
        base_dx=base_dx_C,
        base_sx=base_sx_C,
        altezza_colmo=altezza_colmo,
        interasse=interasse_trapezoidali,
        pendenza_parall=pendenza_parall,
        escludi_displuvio_est=True
    )

    print("\n➡️ Calcolo correntini per falda parallelepipeda D (blocco orizzontale)")
    correntini_falda_D = calcola_correntini_falda_parallelepipedale_L(
        nome_falda="D",
        lunghezza_rettangolo=lunghezza_rettangolo_D,
        base_dx=base_dx_D,
        base_sx=base_sx_D,
        altezza_colmo=altezza_colmo,
        interasse=interasse_trapezoidali,
        pendenza_parall=pendenza_parall,
        escludi_displuvio_est=True


    )

    if tipo_sporto == "1":
        allungamenti = {
            "tri_A": calcola_allungamento_correntino(sporto, pendenza_tri_A),
            "tri_B": calcola_allungamento_correntino(sporto, pendenza_tri_B),
            "trap_A": calcola_allungamento_correntino(sporto, pendenza_trap),
            "trap_B": calcola_allungamento_correntino(sporto, pendenza_trap),
            "parall_C": calcola_allungamento_correntino(sporto, pendenza_parall),
            "parall_D": calcola_allungamento_correntino(sporto, pendenza_parall),
        }
    else:
        allungamenti = {
            "tri_A": 0.0,
            "tri_B": 0.0,
            "trap_A": 0.0,
            "trap_B": 0.0,
            "parall_C": 0.0,
            "parall_D": 0.0,
        }

    stampa_correntini("Triangolare A", correntini_A, allungamenti["tri_A"])
    stampa_correntini("Triangolare B", correntini_B, allungamenti["tri_B"])
    stampa_correntini("Trapezoidale A", correntini_falda_A, allungamenti["trap_A"])
    stampa_correntini("Trapezoidale B", correntini_falda_B, allungamenti["trap_B"])
    stampa_correntini("Parallelepipeda C", correntini_falda_C, allungamenti["parall_C"])
    stampa_correntini("Parallelepipeda D", correntini_falda_D, allungamenti["parall_D"])

    if tipo_sporto == "2":
        lunghezza_passafuori = moltiplicatore_sporto * sporto
        print(f"\n📏 Lunghezza standard passafuori: {lunghezza_passafuori:.2f} m")

        for tipo, posizione, _ in correntini_A:
            print(f"[A (triangolare)] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")
        for tipo, posizione, _ in correntini_B:
            print(f"[B (triangolare)] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")
        for tipo, posizione, _ in correntini_falda_A:
            print(f"[A (trapezoidale)] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")
        for tipo, posizione, _ in correntini_falda_B:
            print(f"[B (trapezoidale)] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")
        for tipo, posizione, _ in correntini_falda_C:
            print(f"[C (parallelepipeda)] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")
        for tipo, posizione, _ in correntini_falda_D:
            print(f"[D (parallelepipeda)] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")

    perimetro = calcola_perimetro_L(lunghezza_A, larghezza_A, lunghezza_B, larghezza_B)
    print(f"\n📐 Perimetro della casa a L: {perimetro:.2f} m")

    if usa_tamponatura:
        lunghezza_tamponatura = perimetro
        print(f"\n📏 Lunghezza tamponatura: {lunghezza_tamponatura:.2f} m")

    lunghezza_correntino_rett_A = next(
        (lunghezza for tipo, _, lunghezza in correntini_falda_A if tipo == "rettangolo"),
        None
    )

    lunghezza_correntino_rett_B = next(
        (lunghezza for tipo, _, lunghezza in correntini_falda_B if tipo == "rettangolo"),
        None
    )

    lunghezza_correntino_rett_C = next(
        (lunghezza for tipo, _, lunghezza in correntini_falda_C if tipo == "rettangolo"),
        None
    )

    lunghezza_correntino_rett_D = next(
        (lunghezza for tipo, _, lunghezza in correntini_falda_D if tipo == "rettangolo"),
        None
    )


    capriata_A = capriata(
        larghezza_casa=larghezza_A,
        correntino_dx=lunghezza_correntino_rett_A,
        correntino_sx=lunghezza_correntino_rett_B,
        altezza_colmo=altezza_colmo,
        pendenza_dx=pendenza_parall,
        pendenza_sx=pendenza_trap,
        nome="Capriata A"
    )

    capriata_B = capriata(
        larghezza_casa=larghezza_B,
        correntino_dx=lunghezza_correntino_rett_C,
        correntino_sx=lunghezza_correntino_rett_D,
        altezza_colmo=altezza_colmo,
        pendenza_dx=pendenza_parall,
        pendenza_sx=pendenza_trap,
        nome="Capriata B"
    )

    # ░▒▓█► AGGIUNTA COMPONENTI ALLA TABELLA ◄█▓▒░

    # Correntini con eventuale allungamento (per sporto classico)
    aggiungi_componenti("Correntino", "Correntino triangolare A", correntini_A, allungamenti["tri_A"])
    aggiungi_componenti("Correntino", "Correntino triangolare B", correntini_B, allungamenti["tri_B"])
    aggiungi_componenti("Correntino", "Correntino trapezoidale A", correntini_falda_A, allungamenti["trap_A"])
    aggiungi_componenti("Correntino", "Correntino trapezoidale B", correntini_falda_B, allungamenti["trap_B"])
    aggiungi_componenti("Correntino", "Correntino parallelepipedo C", correntini_falda_C, allungamenti["parall_C"])
    aggiungi_componenti("Correntino", "Correntino parallelepipedo D", correntini_falda_D, allungamenti["parall_D"])

    aggiungi_componenti("Colmo", "Colmo A", [("lineare", 0, lung_colmo_A)])
    aggiungi_componenti("Colmo", "Colmo B", [("lineare", 0, lung_colmo_B)])
    aggiungi_componenti("Compluvio", "Compluvio centrale", [("lineare", 0, lung_compluvio)])

    aggiungi_componenti("Displuvio", "Displuvio A sinistra", [("lineare", 0, displuvi_lunghezze[0])])
    aggiungi_componenti("Displuvio", "Displuvio A destra", [("lineare", 0, displuvi_lunghezze[1])])
    aggiungi_componenti("Displuvio", "Displuvio B basso", [("lineare", 0, displuvi_lunghezze[2])])
    aggiungi_componenti("Displuvio", "Displuvio B alto", [("lineare", 0, displuvi_lunghezze[3])])
    aggiungi_componenti("Displuvio", "Displuvio centrale", [("lineare", 0, displuvi_lunghezze[4])])

    # Tamponatura (solo se richiesta)
    if usa_tamponatura:
        aggiungi_componenti("Tamponatura", "Tamponatura esterna", [("lineare", 0, perimetro)])

    # Passafuori (solo se tipo sporto == 2)
    if tipo_sporto == "2":
        lunghezza_passafuori = moltiplicatore_sporto * sporto
        lista_passafuori = []

        for falda, lista in [
            ("A", correntini_A),
            ("B", correntini_B),
            ("A", correntini_falda_A),
            ("B", correntini_falda_B),
            ("C", correntini_falda_C),
            ("D", correntini_falda_D)
        ]:
            for _, posizione, _ in lista:
                lista_passafuori.append((falda, posizione, lunghezza_passafuori))

        aggiungi_componenti("Passafuori", "Passafuori esterni", lista_passafuori)

    aggiungi_componenti("Puntone", "Puntone Capriata A", [e for e in capriata_A if e[0] == "Puntone"])
    aggiungi_componenti("Puntone", "Puntone Capriata B", [e for e in capriata_B if e[0] == "Puntone"])

    aggiungi_componenti("Catena", "Catena Capriata A", [e for e in capriata_A if e[0] == "Catena"])
    aggiungi_componenti("Catena", "Catena Capriata B", [e for e in capriata_B if e[0] == "Catena"])

    aggiungi_componenti("Monaco", "Monaco Capriata A", [e for e in capriata_A if e[0] == "Monaco"])
    aggiungi_componenti("Monaco", "Monaco Capriata B", [e for e in capriata_B if e[0] == "Monaco"])

    aggiungi_componenti("Saetta", "Saetta Capriata A", [e for e in capriata_A if e[0] == "Saetta"])
    aggiungi_componenti("Saetta", "Saetta Capriata B", [e for e in capriata_B if e[0] == "Saetta"])


    # ► Stampa finale
    print("\n📦 Tabella componenti generata:")
    global tabella_componenti
    tabella_componenti = completa_tabella_componenti(tabella_componenti)
    print(tabella_componenti)
    # dopo tutte le chiamate a aggiungi_componenti:
    df = pd.DataFrame(tabella_componenti)
    # salva CSV o Excel
    df.to_csv("tabella_componenti.csv", index=False)
    df.to_excel("tabella_componenti.xlsx", index=False)
    print("File salvati: tabella_componenti.csv e .xlsx")

    dati_preventivo = chiedi_dati_preventivo()


    genera_report_completo(
        nome_file_pdf="report_preventivo.pdf",
        tabella_componenti=tabella_componenti,
        path_logo="Logo_Cavanna_Strutture.png",  # <-- nome corretto
        path_disegno="disegno2d_temp.png",
        dati_preventivo=dati_preventivo
    )

    os.remove("disegno2d_temp.png")

    visualizza_tetto_L_3d_completo(
        h_colmo= altezza_colmo,
        spostamento_colmo_A=spostamento_colmo_A,
        spostamento_colmo_B=spostamento_colmo_B,
        lar_A=larghezza_A, lar_B=larghezza_B, lun_A=lunghezza_A, lun_B=lunghezza_B,
        taglio_A=taglio_A, taglio_B=taglio_B,
        interasse_triangolari=interasse_triangolari,
        interasse_trapezoidali=interasse_trapezoidali

    )







def disegna_tetto_L_2d_completo(lun_A, lar_A, lun_B, lar_B,
                                pendenza_tri_A, pendenza_tri_B,
                                pendenza_trap, pendenza_parall, interasse_triangolari, interasse_trapezoidali, ):
    import matplotlib.pyplot as plt
    import math

    fig, ax = plt.subplots(figsize=(10, 8))

    # Coordinate blocchi
    x0, y0 = 0, 0
    A_x0, A_y0 = x0, y0 + lar_B
    A_x1, A_y1 = A_x0 + lar_A, A_y0 + lun_A
    B_x0, B_y0 = x0 + lar_A, y0
    B_x1, B_y1 = B_x0 + lun_B, B_y0 + lar_B

    # Contorno L
    contorno = [
        (x0, y0), (B_x1, y0), (B_x1, B_y1), (B_x0, B_y1),
        (B_x0, A_y0), (A_x1, A_y0), (A_x1, A_y1), (x0, A_y1), (x0, y0)
    ]
    x_cont, y_cont = zip(*contorno)
    ax.plot(x_cont, y_cont, 'k-', lw=2, label='Perimetro casa')

    # Altezza colmo
    h_trap = math.tan(math.radians(pendenza_trap)) * (lar_A / 2)
    h_parall = math.tan(math.radians(pendenza_parall)) * (lar_B / 2)
    h_colmo = (h_trap + h_parall) / 2

    # Spostamenti dovuti alle pendenze (corretti: trapeziodale verso esterno)
    dx_trap = h_colmo / math.tan(math.radians(pendenza_trap))
    dx_parall = h_colmo / math.tan(math.radians(pendenza_parall))

    # Nodo colmo corretto
    delta = (dx_trap - dx_parall) / 2
    nodo_colmo_x = x0 + lar_A / 2 + delta
    nodo_colmo_y = y0 + lar_B / 2 + delta

    # Tagli per falde triangolari
    taglio_A = h_colmo / math.tan(math.radians(pendenza_tri_A))
    taglio_B = h_colmo / math.tan(math.radians(pendenza_tri_B))

    # Colmo A (verticale)
    colmo_A_top = (nodo_colmo_x, y0 + lar_B + lun_A - taglio_A)
    colmo_A_bot = (nodo_colmo_x, y0 + lar_B + taglio_A)

    # Colmo B (orizzontale)
    colmo_B_left = (x0 + lar_A + taglio_B, nodo_colmo_y)
    colmo_B_right = (x0 + lar_A + lun_B - taglio_B, nodo_colmo_y)

    # Compluvio
    angolo_interno = (x0 + lar_A, y0 + lar_B)

    # Disegno colmi
    ax.plot([colmo_A_top[0], nodo_colmo_x], [colmo_A_top[1], nodo_colmo_y], 'r-', lw=2.5, label='Colmo A')
    ax.plot([colmo_B_right[0], nodo_colmo_x], [colmo_B_right[1], nodo_colmo_y], 'r-', lw=2.5, label='Colmo B')

    # Compluvio
    ax.plot([nodo_colmo_x, angolo_interno[0]], [nodo_colmo_y, angolo_interno[1]], 'g-', lw=2.5, label='Compluvio')

    # Displuvi triangolari + centrale + esterno
    displuvi = [
        ((x0, y0 + lar_B + lun_A), colmo_A_top),              # triangolare A sx
        ((x0 + lar_A, y0 + lar_B + lun_A), colmo_A_top),      # triangolare A dx
        ((x0 + lar_A + lun_B, y0), colmo_B_right),            # triangolare B dx
        ((x0 + lar_A + lun_B, y0 + lar_B), colmo_B_right),    # triangolare B alto dx
        ((x0, y0), (nodo_colmo_x, nodo_colmo_y))              # diagonale centrale displuvio
    ]
    for p1, p2 in displuvi:
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'b-', lw=1.5)

    print("✅ Disegno 2D tetto a L completato.")
    # 🔍 Calcolo spostamento colmo per falda A (verticale, asse X)
    x_base_sx_A = x0
    x_base_dx_A = x0 + lar_A
    x_centro_base_A = (x_base_sx_A + x_base_dx_A) / 2
    spostamento_colmo_A = nodo_colmo_x - x_centro_base_A
    print(f"\n📐 Spostamento colmo per falda A (asse X): {spostamento_colmo_A:.3f} m")

    # 🔍 Calcolo spostamento colmo per falda B (orizzontale, asse Y)
    y_base_sotto_B = y0
    y_base_sopra_B = y0 + lar_B
    y_centro_base_B = (y_base_sotto_B + y_base_sopra_B) / 2
    spostamento_colmo_B = nodo_colmo_y - y_centro_base_B
    print(f"📐 Spostamento colmo per falda B (asse Y): {spostamento_colmo_B:.3f} m")


    # 🔷 Falda triangolare A (sx)
    falda_tri_A = [(x0, y0 + lar_B + lun_A), (x0 + lar_A / 2 + spostamento_colmo_A, y0 + lar_B + lun_A - taglio_A),
                   (x0 + lar_A, y0 + lar_B + lun_A)]

    # 🔷 Falda triangolare B (dx)
    falda_tri_B = [(x0 + lar_A + lun_B, y0 + lar_B), (x0 + lar_A + lun_B - taglio_B, y0 + lar_B / 2 + spostamento_colmo_B),
                   (x0 + lar_A + lun_B, y0)]

    # 🔷 Falda trapezoidale A (verticale)
    falda_trap_A = [
    (x0, y0),                    # angolo basso
    (x0 + lar_A/2 + spostamento_colmo_A,y0 + lar_B / 2 + spostamento_colmo_B),                # base colmo bassa
    colmo_A_top,                # colmo alto
    (x0, y0 + lun_A + lar_B)    # angolo alto
]




    # 🔷 Falda trapezoidale B (orizzontale)
    falda_trap_B = [
    (x0 , y0),
    (x0 + lar_A + lun_B , y0),
    (x0 + lar_A + lun_B - taglio_B, y0 + lar_B / 2 + spostamento_colmo_B),
    (x0 + lar_A/2 + spostamento_colmo_A, y0 + lar_B / 2 + spostamento_colmo_B)
]

    # 🔷 Falda parallelepipedo C (sotto)
    falda_parall_C = [
    (x0 + lar_A/2 +spostamento_colmo_A, y0 + lar_B/2 + spostamento_colmo_B),
    (x0 + lar_A, y0 + lar_B),
    (x0 + lar_A, y0 + lar_B + lun_A),
    (x0 + lar_A/2 +spostamento_colmo_A, y0 + lar_B + lun_A - taglio_A)
]

    # 🔷 Falda parallelepipedo D (sopra)
    falda_parall_D =  [
    (x0 + lar_A/2 +spostamento_colmo_A, y0 + lar_B/2 +spostamento_colmo_B),
    (x0 + lar_A + lun_B - taglio_B, y0 + lar_B/2 +spostamento_colmo_B),
    (x0 + lar_A +lun_B, y0 + lar_B ),
    (x0 + lar_A , y0 + lar_B )
]


    riempi_falda_con_linee(ax, falda_tri_A, orientamento='verticale', interasse=interasse_triangolari)
    riempi_falda_con_linee(ax, falda_tri_B, orientamento='orizzontale', interasse=interasse_triangolari)
    riempi_falda_con_linee(ax, falda_trap_A, orientamento='orizzontale', interasse=interasse_trapezoidali)
    riempi_falda_con_linee(ax, falda_trap_B, orientamento='verticale', interasse=interasse_trapezoidali)
    riempi_falda_con_linee(ax, falda_parall_C, orientamento='orizzontale', interasse=interasse_trapezoidali)
    riempi_falda_con_linee(ax, falda_parall_D, orientamento='verticale', interasse=interasse_trapezoidali)



    plt.savefig("disegno2d_temp.png", dpi=300)



    ax.set_aspect('equal')
    ax.set_title("Vista in pianta - Tetto a L")
    ax.set_xlabel("X (metri)")
    ax.set_ylabel("Y (metri)")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    plt.tight_layout()
    plt.show()

    return colmo_A_top, (nodo_colmo_x, nodo_colmo_y), colmo_B_right, angolo_interno, displuvi, h_colmo, spostamento_colmo_A, spostamento_colmo_B


def disegna_tetto_due_falde_2d(lato_lungo, lato_corto, altezza_colmo, interasse, posizione_colmo=0, mostra_rompitratta_sx=False, mostra_rompitratta_dx=False):
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    import numpy as np

    fig, ax = plt.subplots(figsize=(10, 6))

    metà_lato_lungo = lato_lungo / 2
    metà_lato_corto = lato_corto / 2

    casa_x = [-metà_lato_lungo, metà_lato_lungo, metà_lato_lungo, -metà_lato_lungo, -metà_lato_lungo]
    casa_y = [-metà_lato_corto, -metà_lato_corto, metà_lato_corto, metà_lato_corto, -metà_lato_corto]
    ax.plot(casa_x, casa_y, 'k--', label='Contorno casa')

    # Colmo lungo tutto il lato lungo
    colmo_y = posizione_colmo
    ax.plot([-metà_lato_lungo, metà_lato_lungo], [colmo_y, colmo_y], 'r-', linewidth=2.5, label='Colmo')

    if mostra_rompitratta_sx:
        # Rompitratta falda nord (sinistra)
        y_rompitratta_sx = posizione_colmo + (metà_lato_corto - posizione_colmo) / 2
        ax.plot([-metà_lato_lungo, metà_lato_lungo], [y_rompitratta_sx, y_rompitratta_sx],
                'g--', linewidth=2, label='Rompitratta SX')

    if mostra_rompitratta_dx:
        # Rompitratta falda sud (destra)
        y_rompitratta_dx = posizione_colmo - (posizione_colmo + metà_lato_corto) / 2
        ax.plot([-metà_lato_lungo, metà_lato_lungo], [y_rompitratta_dx, y_rompitratta_dx],
                'g--', linewidth=2, label='Rompitratta DX')


    # Falde
    falda_sx = [(-metà_lato_lungo, -metà_lato_corto), (-metà_lato_lungo, metà_lato_corto), (-metà_lato_lungo, posizione_colmo)]
    falda_dx = [(metà_lato_lungo, -metà_lato_corto), (metà_lato_lungo, metà_lato_corto), (metà_lato_lungo, posizione_colmo)]

    # Correntini
    x = -metà_lato_lungo
    while x <= metà_lato_lungo:
        ax.plot([x, x], [-metà_lato_corto, metà_lato_corto], 'm-', lw=0.8)
        x += interasse

    ax.set_aspect('equal')
    ax.set_title("Vista in pianta - Tetto a due falde")
    ax.set_xlabel("X (metri)")
    ax.set_ylabel("Y (metri)")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    plt.tight_layout()
    fig.savefig("tetto_due_falde_2D.png", dpi=300)

    plt.savefig("disegno2d_temp.png", dpi=300)

    plt.show()






def disegna_tetto_due_falde_3d(lato_lungo, lato_corto, altezza_colmo, interasse, posizione_colmo=0, mostra_rompitratta_sx=False, mostra_rompitratta_dx=False, pendenza_sx=19, pendenza_dx=19):

    # Calcolo metà dimensioni
    metà_lato_lungo = lato_lungo / 2
    metà_lato_corto = lato_corto / 2

    # Vertici base casa
    A = [-metà_lato_lungo, -metà_lato_corto, 0]
    B = [metà_lato_lungo, -metà_lato_corto, 0]
    C = [metà_lato_lungo, metà_lato_corto, 0]
    D = [-metà_lato_lungo, metà_lato_corto, 0]

    # Vertici colmo (posizione centrale lungo y)
    E = [-metà_lato_lungo, posizione_colmo, altezza_colmo]
    F = [metà_lato_lungo, posizione_colmo, altezza_colmo]

    # Array vertici
    vertices = np.array([A, B, C, D, E, F])
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]

    # Facce del tetto: due triangoli per falda
    faces = [
        [0, 1, 5], [0, 5, 4],  # Falda sud
        [3, 2, 5], [3, 5, 4],  # Falda nord
    ]
    i, j, k = zip(*faces)

    fig = go.Figure()

    # Aggiunge mesh tetto
    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color='lightgray',
        opacity=1.0,
        flatshading=True,
        name='Falde'
    ))

    # Linea colmo
    fig.add_trace(go.Scatter3d(
        x=[E[0], F[0]], y=[E[1], F[1]], z=[E[2], F[2]],
        mode='lines',
        line=dict(color='red', width=6),
        name='Colmo'
    ))

    metà_lato_corto = lato_corto / 2

    # Rompitratta sinistro
    if mostra_rompitratta_sx:
        y_r = posizione_colmo - (lato_corto / 4)
        d_sx = abs(y_r - posizione_colmo)
        d_colmo_gronda_sx = abs(-metà_lato_corto - posizione_colmo)
        z_r = altezza_colmo * (1 - d_sx / d_colmo_gronda_sx)
        fig.add_trace(go.Scatter3d(
            x=[-lato_lungo / 2, lato_lungo / 2],
            y=[y_r, y_r],
            z=[z_r, z_r],
            mode='lines',
            line=dict(color='green', width=4),
            name='Rompitratta SX'
        ))

    # Rompitratta destro
    if mostra_rompitratta_dx:
        y_r = posizione_colmo + (lato_corto / 4)
        d_dx = abs(y_r - posizione_colmo)
        d_colmo_gronda_dx = abs(metà_lato_corto - posizione_colmo)
        z_r = altezza_colmo * (1 - d_dx / d_colmo_gronda_dx)
        fig.add_trace(go.Scatter3d(
            x=[-lato_lungo / 2, lato_lungo / 2],
            y=[y_r, y_r],
            z=[z_r, z_r],
            mode='lines',
            line=dict(color='green', width=4),
            name='Rompitratta DX'
        ))

    # Correntini su entrambe le falde
    falda_sud = [A, B, F, E]
    falda_nord = [D, C, F, E]

    riempi_falda_con_linee_3d(fig, falda_sud, orientamento='verticale', interasse=interasse, colore='black')
    riempi_falda_con_linee_3d(fig, falda_nord, orientamento='verticale', interasse=interasse, colore='black')

    # Layout 3D
    fig.update_layout(
        title="Tetto 3D a Due Falde",
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, t=40, b=0)
    )

    # Salva ed apri in browser
    output_path = "tetto_due_falde_3D.html"
    fig.write_html(output_path)
    print(f"✅ Visualizzazione salvata in '{output_path}'")
    #webbrowser.open("file://" + os.path.abspath(output_path))










def disegna_tetto_monofalda_2d(lato_lungo, lato_corto, altezza_colmo, orientamento_corto, mostra_rompitratta=False):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))

    # Coordinate base casa (rettangolo)
    casa = [
        (-lato_lungo / 2, -lato_corto / 2),
        (lato_lungo / 2, -lato_corto / 2),
        (lato_lungo / 2, lato_corto / 2),
        (-lato_lungo / 2, lato_corto / 2),
        (-lato_lungo / 2, -lato_corto / 2)
    ]

    casa_x, casa_y = zip(*casa)
    ax.plot(casa_x, casa_y, 'k--', label='Casa')

    # Coordinate colmo (linea superiore inclinata)
    if orientamento_corto == "nord-sud":
        colmo_y = lato_corto / 2
        gronda_y = -lato_corto / 2
        colmo_label = "Nord"
        gronda_label = "Sud"
    else:
        colmo_y = lato_corto / 2
        gronda_y = -lato_corto / 2
        colmo_label = "Ovest"
        gronda_label = "Est"

    # Falda inclinata: colmo in alto (tutto il lato_lungo)
    ax.plot([-lato_lungo / 2, lato_lungo / 2], [colmo_y, colmo_y], 'r-', lw=2.5, label='Colmo')
    ax.plot([-lato_lungo / 2, lato_lungo / 2], [gronda_y, gronda_y], 'b-', lw=2.5, label='Gronda')

    if mostra_rompitratta:
        y_rompitratta = (colmo_y + gronda_y) / 2
        ax.plot([-lato_lungo / 2, lato_lungo / 2], [y_rompitratta, y_rompitratta], 'g--', linewidth=2, label='Rompitratta')

    # Correntini inclinati
    x_start = -lato_lungo / 2
    x = x_start
    interasse = suggerisci_interasse_ottimale(lato_lungo)

    while x <= lato_lungo / 2:
        ax.plot([x, x], [gronda_y, colmo_y], 'm-', lw=0.8)
        x += interasse

    ax.text(0, colmo_y + 1, colmo_label, ha='center', fontsize=12, weight='bold')
    ax.text(0, gronda_y - 1.2, gronda_label, ha='center', fontsize=12, weight='bold')

    ax.set_aspect('equal')
    ax.set_title("Vista in pianta - Tetto a monofalda", fontsize=14)
    ax.set_xlabel("X (metri)")
    ax.set_ylabel("Y (metri)")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    plt.tight_layout()

    plt.savefig("disegno2d_temp.png", dpi=300)


    plt.show()

    print("✅ Disegno 2D tetto a monofalda completato.")

def disegna_tetto_monofalda_3d(lato_lungo, lato_corto, altezza_colmo, interasse, verso="nord", mostra_rompitratta=False):
    import plotly.graph_objects as go
    import numpy as np
    import os
    import webbrowser

    # Centro casa
    metà_lato_lungo = lato_lungo / 2
    metà_lato_corto = lato_corto / 2

    # Angoli base
    A = [-metà_lato_lungo, -metà_lato_corto, 0]
    B = [metà_lato_lungo, -metà_lato_corto, 0]
    C = [metà_lato_lungo, metà_lato_corto, 0]
    D = [-metà_lato_lungo, metà_lato_corto, 0]

    # Colmo (punto alto della falda)
    if verso == "nord":
        E = [-metà_lato_lungo, metà_lato_corto, altezza_colmo]
        F = [metà_lato_lungo, metà_lato_corto, altezza_colmo]
        falda_vertices = [A, B, F, E]
        muro_vertices = [D, C, F, E]
        falda_faces = [[0, 1, 5], [0, 5, 4]]
        muro_faces = [[3, 2, 5], [3, 5, 4]]
    else:
        E = [-metà_lato_lungo, -metà_lato_corto, altezza_colmo]
        F = [metà_lato_lungo, -metà_lato_corto, altezza_colmo]
        falda_vertices = [D, C, F, E]
        muro_vertices = [A, B, F, E]
        falda_faces = [[3, 2, 5], [3, 5, 4]]
        muro_faces = [[0, 1, 5], [0, 5, 4]]

    vertices = np.array([A, B, C, D, E, F])
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]

    fig = go.Figure()

    # Falda inclinata (marrone)
    i_falda, j_falda, k_falda = zip(*falda_faces)
    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z,
        i=i_falda, j=j_falda, k=k_falda,
        color='lightgray',
        opacity=1.0,
        flatshading=True,
        name='Falda'
    ))

    # Muro verticale (azzurro)
    i_muro, j_muro, k_muro = zip(*muro_faces)
    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z,
        i=i_muro, j=j_muro, k=k_muro,
        color='lightblue',
        opacity=1.0,
        flatshading=True,
        name='Muro'
    ))

    # Colmo
    fig.add_trace(go.Scatter3d(
        x=[E[0], F[0]], y=[E[1], F[1]], z=[E[2], F[2]],
        mode='lines',
        line=dict(color='red', width=6),
        name='Colmo'
    ))
    if mostra_rompitratta:
        # Rompitratta (a metà altezza tra gronda e colmo)
        x_start = E[0]
        x_end = F[0]
        y_rompitratta = E[1]  # stessa Y del colmo (cioè lato_corto/2 o -lato_corto/2)
        z_rompitratta = altezza_colmo / 2  # a metà altezza

        fig.add_trace(go.Scatter3d(
            x=[x_start, x_end],
            y=[0, 0],
            z=[z_rompitratta, z_rompitratta],
            mode='lines',
            line=dict(color='green', width=4),
            name='Rompitratta'
        ))


    # Correntini
    riempi_falda_con_linee_3d(fig, falda_vertices, orientamento='verticale', interasse=interasse, colore='black')

    fig.update_layout(
        title="Tetto 3D a Monofalda",
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, t=40, b=0)
    )

    fig.write_html("tetto_monofalda_3d.html")
    print("✅ Visualizzazione salvata in 'tetto_monofalda_3d.html'. Apri il file nel browser.")
    webbrowser.open("file://" + os.path.abspath("tetto_monofalda_3d.html"))


#gestione tetto tre falde

def gestisci_tetto_tre_falde(lato_lungo, lato_corto, sporto=0.0, tipo_sporto=None, usa_tamponatura = False, orientamento_corto =""):
    print("\n--- CONFIGURAZIONE TETTO A 3 FALDE ---")
    # Scegli su quale lato CORTO sta la falda triangolare, coerente con l'orientamento
    if orientamento_corto == "nord-sud":
        lato_tri = input("Falda triangolare su quale lato corto? (Nord/Sud): ").strip().lower()
        lato_tri = "nord" if lato_tri not in ("nord", "sud") else lato_tri
        label_tri = f"Falda triangolare ({'Nord' if lato_tri == 'nord' else 'Sud'})"
        label_trap_sx = "Falda trapezoidale sinistra (Est)"
        label_trap_dx = "Falda trapezoidale destra (Ovest)"
    else:  # est-ovest
        lato_tri = input("Falda triangolare su quale lato corto? (Est/Ovest): ").strip().lower()
        lato_tri = "est" if lato_tri not in ("est", "ovest") else lato_tri
        label_tri = f"Falda triangolare ({'Est' if lato_tri == 'est' else 'Ovest'})"
        label_trap_sx = "Falda trapezoidale sinistra (Nord)"
        label_trap_dx = "Falda trapezoidale destra (Sud)"

    # Pendenze: una triangolare + due trapezoidali
    pendenza_tri = chiedi_pendenza(label_tri)
    pendenza_trap_sx = chiedi_pendenza(label_trap_sx)
    pendenza_trap_dx = chiedi_pendenza(label_trap_dx)

    # 1) Altezza colmo: dalle TRAPEZOIDALI sul lato CORTO
    posizione_colmo, altezza_colmo = calcola_posizione_colmo(pendenza_trap_sx, pendenza_trap_dx, lato_corto)

    # 2) Taglio del colmo: UNA sola triangolare
    taglio_tri = altezza_colmo / math.tan(math.radians(pendenza_tri))

    # 3) Lunghezza colmo con pre-check
    lunghezza_colmo = lato_lungo - taglio_tri

    print(f"[DEBUG] lato_lungo={lato_lungo}, lato_corto={lato_corto}, orientamento_corto={orientamento_corto}")
    print(f"[DEBUG] altezza_colmo={altezza_colmo:.3f}")
    print(f"[DEBUG] taglio_tri={taglio_tri:.3f}")
    print(f"[DEBUG] lunghezza_colmo={lunghezza_colmo:.3f}")

    if lunghezza_colmo <= 0:
        print("\n❌ Il tetto a 3 falde così NON chiude bene: colmo ≤ 0 (il colmo scompare).")
        if lato_lungo > 0 and altezza_colmo > 0:
            phi_min = math.degrees(math.atan(altezza_colmo / lato_lungo))
            print(f"   🔧 Suggerimento: con le trapezoidali attuali, servirebbe TRIANGOLARE ≳ {phi_min:.1f}°.")
            print("   Alternative: riduci le trapezoidali oppure cambia orientamento (o il lato triangolare).")

            scelta = input(f"\nVuoi procedere impostando la triangolare a {phi_min:.1f}°? (S/n): ").strip().lower()
            if scelta == "s":
                pendenza_tri = phi_min
                taglio_tri = altezza_colmo / math.tan(math.radians(pendenza_tri))
                lunghezza_colmo = lato_lungo - taglio_tri
                colmo_zero = True
                print(f"✅ Triangolare aggiornata a {phi_min:.1f}°. Nuova lunghezza colmo: {lunghezza_colmo:.2f} m")
            else:
                print("Interruzione configurazione tetto a 3 falde.\n")
                return  # se l'utente rifiuta, qui interrompi

    interasse_trapezio_suggerito = suggerisci_interasse_ottimale(lunghezza_colmo)
    print(f"\n[Consiglio] Interasse consigliato per falde trapezoidali: {interasse_trapezio_suggerito:.2f} m")
    usa_default = input(f"Usare questo interasse? (S/n): ").strip().lower()
    if usa_default == "n":
        try:
            interasse_trapezoidali = float(input("Inserisci interasse personalizzato per le trapezoidali: "))
        except ValueError:
            print("Valore non valido. Uso quello suggerito.")
            interasse_trapezoidali = interasse_trapezio_suggerito
    else:
        interasse_trapezoidali = interasse_trapezio_suggerito

    usa_stesso = input(f"\nVuoi usare lo stesso interasse ({interasse_trapezoidali:.2f}) anche per la falda triangolare? (S/n): ").strip().lower()
    if usa_stesso == "n":
        try:
            interasse_triangolare = float(input("Inserisci interasse per la falda triangolare: "))
        except ValueError:
            interasse_triangolare = interasse_trapezoidali
    else:
        interasse_triangolare = interasse_trapezoidali

    base_sx = (lato_corto / 2) + posizione_colmo
    base_dx = (lato_corto / 2) - posizione_colmo

    if colmo_zero == True:
        correntini_sud = calcola_correntini_falda_trapezoidale(
            "Sud", lato_lungo, base_sx, base_dx, altezza_colmo, interasse_trapezoidali, 0, taglio_tri, escludi_displuvio_est=False)
        correntini_nord = calcola_correntini_falda_trapezoidale(
            "Nord", lato_lungo, base_dx, base_sx, altezza_colmo, interasse_trapezoidali, 0, taglio_tri, escludi_displuvio_est=False
        )
    else:
        correntini_sud = calcola_correntini_falda_trapezoidale(
            "Sud", lato_lungo, base_sx, base_dx, altezza_colmo, interasse_trapezoidali, 0, taglio_tri,
            escludi_displuvio_est=True)
        correntini_nord = calcola_correntini_falda_trapezoidale(
            "Nord", lato_lungo, base_dx, base_sx, altezza_colmo, interasse_trapezoidali, 0, taglio_tri,
            escludi_displuvio_est=True
        )
    correntini_tri = calcola_correntini_falda_triangolare(
        "Est", lato_corto, altezza_colmo, taglio_tri, interasse_triangolare
    )

    if tipo_sporto == "1":
        allungamento_tri = calcola_allungamento_correntino(sporto, pendenza_tri)
        allungamento_trap_sx = calcola_allungamento_correntino(sporto, pendenza_trap_sx)
        allungamento_trap_dx = calcola_allungamento_correntino(sporto, pendenza_trap_dx)
    else:
        allungamento_tri = allungamento_trap_sx = allungamento_trap_dx = 0.0

    print("\n--- Correntini finali con sporto ---")

    for tipo, pos, lung in correntini_tri:
        finale = lung + allungamento_tri
        print(f"[TRIANGOLARE] Pos {pos:.2f} m | Base: {lung:.2f} m → Totale: {finale:.2f} m")

    for tipo, pos, lung in correntini_sud:
        finale = lung + allungamento_trap_sx
        print(f"[SUD] Pos {pos:.2f} m | Base: {lung:.2f} m → Totale: {finale:.2f} m")

    for tipo, pos, lung in correntini_nord:
        finale = lung + allungamento_trap_dx
        print(f"[NORD] Pos {pos:.2f} m | Base: {lung:.2f} m → Totale: {finale:.2f} m")

    if tipo_sporto == "2":
        lunghezza_passafuori = moltiplicatore_sporto * sporto
        print(f"\n📏 Lunghezza passafuori: {lunghezza_passafuori:.2f} m")

        for tipo, posizione, _ in correntini_tri:
            print(f"[TRIANGOLARE] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")
        for tipo, posizione, _ in correntini_sud:
            print(f"[TRAPEZOIDALE SUD] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")
        for tipo, posizione, _ in correntini_nord:
            print(f"[TRAPEZOIDALE NORD] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")

    print("\n--- RISULTATI ---")
    print(f"Tipo di tetto: 3 falde (2 trapezoidali + 1 triangolare)")
    print(f"Lunghezza colmo: {lunghezza_colmo:.2f} m")
    print(f"Altezza colmo: {altezza_colmo:.2f} m")

    if posizione_colmo == 0:
        print("Il colmo è al centro della casa.")
    else:
        direzione = "destra" if posizione_colmo < 0 else "sinistra"
        print(f"Il colmo è spostato di {abs(posizione_colmo):.2f} m verso {direzione}.")

    perimetro = calcola_perimetro_rettangolare(lato_lungo, lato_corto)
    print(f"\n📐 Perimetro della casa: {perimetro:.2f} m")

    if usa_tamponatura:
        lunghezza_tamponatura = perimetro
        print(f"\n📏 Lunghezza tamponatura: {lunghezza_tamponatura:.2f} m")

    lunghezza_correntino_rett_dx = next(
        (lunghezza for tipo, _, lunghezza in correntini_nord if tipo == "rettangolo"),
        None
    )

    lunghezza_correntino_rett_sx = next(
        (lunghezza for tipo, _, lunghezza in correntini_sud if tipo == "rettangolo"),
        None
    )





    H_tri = math.sqrt(taglio_tri ** 2 + altezza_colmo ** 2)
    metà_lato_corto = lato_corto / 2

    B_est_dx = metà_lato_corto - posizione_colmo  # Nord-Est
    B_est_sx = metà_lato_corto + posizione_colmo  # Sud-Est

    displuvio_est_dx = math.sqrt(H_tri ** 2 + B_est_dx ** 2)
    displuvio_est_sx = math.sqrt(H_tri ** 2 + B_est_sx ** 2)

    meta = lato_corto / 2
    B_ovest_dx = meta - posizione_colmo  # Nord-Ovest
    B_ovest_sx = meta + posizione_colmo  # Sud-Ovest

    displuvio_ovest_dx = math.sqrt(altezza_colmo ** 2 + B_ovest_dx ** 2)
    displuvio_ovest_sx = math.sqrt(altezza_colmo ** 2 + B_ovest_sx ** 2)


    if colmo_zero == True:
        capriata_var = capriata(
            larghezza_casa=lato_corto,
            correntino_dx=displuvio_ovest_dx,
            correntino_sx=displuvio_ovest_sx,
            altezza_colmo=altezza_colmo,
            pendenza_dx=pendenza_trap_dx,
            pendenza_sx=pendenza_trap_sx,
            nome="Capriata"
        )

    else:
        capriata_var = capriata(
            larghezza_casa=lato_corto,
            correntino_dx=lunghezza_correntino_rett_dx,
            correntino_sx=lunghezza_correntino_rett_sx,
            altezza_colmo=altezza_colmo,
            pendenza_dx=pendenza_trap_dx,
            pendenza_sx=pendenza_trap_sx,
            nome="Capriata"
        )





    # Disegno
    disegna_tetto_3_falde_2d(lato_lungo, lato_corto, posizione_colmo, altezza_colmo,
                             interasse_trapezoidali, interasse_triangolare, taglio_tri)


    # ░▒▓█► AGGIUNTA COMPONENTI ALLA TABELLA ◄█▓▒░

    # Correntini con eventuale allungamento (per sporto classico)
    aggiungi_componenti("Correntino", "Correntino triangolare EST", correntini_tri, allungamento_tri)
    aggiungi_componenti("Correntino", "Correntino trapezoidale NORD", correntini_nord, allungamento_trap_dx)
    aggiungi_componenti("Correntino", "Correntino trapezoidale SUD", correntini_sud, allungamento_trap_sx)

    aggiungi_componenti("Colmo", "Colmo", [("lineare", 0, lunghezza_colmo)])


    aggiungi_componenti("Displuvio", "Displuvio nord-est", [("lineare", 0, displuvio_est_dx)])
    aggiungi_componenti("Displuvio", "Displuvio sud-est", [("lineare", 0, displuvio_est_sx)])


    # Tamponatura (solo se richiesta)
    if usa_tamponatura:
        aggiungi_componenti("Tamponatura", "Tamponatura esterna", [("lineare", 0, perimetro)])

    # Passafuori (solo se tipo sporto == 2)
    if tipo_sporto == "2":
        lunghezza_passafuori = moltiplicatore_sporto * sporto
        lista_passafuori = []

        for falda, lista in [
            ("Est", correntini_tri),
            ("Sud", correntini_sud),
            ("Nord", correntini_nord)
        ]:
            for _, posizione, _ in lista:
                lista_passafuori.append((falda, posizione, lunghezza_passafuori))

        aggiungi_componenti("Passafuori", "Passafuori esterni", lista_passafuori)

    aggiungi_componenti("Puntone", "Puntone Capriata", [e for e in capriata_var if e[0] == "Puntone"])

    aggiungi_componenti("Catena", "Catena Capriata", [e for e in capriata_var if e[0] == "Catena"])

    aggiungi_componenti("Monaco", "Monaco Capriata", [e for e in capriata_var if e[0] == "Monaco"])

    aggiungi_componenti("Saetta", "Saetta Capriata", [e for e in capriata_var if e[0] == "Saetta"])

    # ► Stampa finale
    print("\n📦 Tabella componenti generata:")
    global tabella_componenti
    tabella_componenti = completa_tabella_componenti(tabella_componenti)
    print(tabella_componenti)
    # dopo tutte le chiamate a aggiungi_componenti:
    df = pd.DataFrame(tabella_componenti)
    # salva CSV o Excel
    df.to_csv("tabella_componenti.csv", index=False)
    df.to_excel("tabella_componenti.xlsx", index=False)
    print("File salvati: tabella_componenti.csv e .xlsx")

    dati_preventivo = chiedi_dati_preventivo()

    genera_report_completo(
        nome_file_pdf="report_preventivo.pdf",
        tabella_componenti=tabella_componenti,
        path_logo="Logo_Cavanna_Strutture.png",  # <-- nome corretto
        path_disegno="disegno2d_temp.png",
        dati_preventivo=dati_preventivo
    )

    os.remove("disegno2d_temp.png")

    disegna_tetto_3_falde_3d(lato_lungo, lato_corto, posizione_colmo, altezza_colmo,
                             interasse_trapezoidali, interasse_triangolare, taglio_tri)


# ✅ DISEGNO 2D PER TETTO A 3 FALDE

def disegna_tetto_3_falde_2d(lato_lungo, lato_corto, posizione_colmo, altezza_colmo,
                             interasse_trapezoidali, interasse_triangolare, taglio_tri):
    import matplotlib.pyplot as plt
    from matplotlib.path import Path

    fig, ax = plt.subplots(figsize=(10, 7))
    metà_lato_lungo = lato_lungo / 2
    metà_lato_corto = lato_corto / 2

    colmo_x_ini = - (lato_lungo / 2)
    colmo_x_fine = (lato_lungo / 2 - taglio_tri)
    colmo_y = posizione_colmo

    casa_x = [-metà_lato_lungo, metà_lato_lungo, metà_lato_lungo, -metà_lato_lungo, -metà_lato_lungo]
    casa_y = [-metà_lato_corto, -metà_lato_corto, metà_lato_corto, metà_lato_corto, -metà_lato_corto]
    ax.plot(casa_x, casa_y, 'k--', linewidth=1, label='Contorno casa')

    # Colmo
    ax.plot([colmo_x_ini, colmo_x_fine], [colmo_y, colmo_y], 'r-', linewidth=2.5, label='Colmo')

    # Displuvi
    ax.plot([colmo_x_ini, -metà_lato_lungo], [colmo_y, metà_lato_corto], 'b-', linewidth=1.5)
    ax.plot([colmo_x_ini, -metà_lato_lungo], [colmo_y, -metà_lato_corto], 'b-', linewidth=1.5)
    ax.plot([colmo_x_fine, metà_lato_lungo], [colmo_y, metà_lato_corto], 'b-', linewidth=1.5)
    ax.plot([colmo_x_fine, metà_lato_lungo], [colmo_y, -metà_lato_corto], 'b-', linewidth=1.5)

    # Falde
    nord = [(colmo_x_ini, colmo_y), (colmo_x_fine, colmo_y), (metà_lato_lungo, -metà_lato_corto),
            (-metà_lato_lungo, -metà_lato_corto)]
    sud = [(colmo_x_ini, colmo_y), (colmo_x_fine, colmo_y), (metà_lato_lungo, metà_lato_corto),
           (-metà_lato_lungo, metà_lato_corto)]
    est = [(colmo_x_fine, colmo_y), (metà_lato_lungo, -metà_lato_corto), (metà_lato_lungo, metà_lato_corto)]

    start_vert = 0
    start_horiz = posizione_colmo

    riempi_falda_con_linee(ax, nord, 'verticale', interasse_trapezoidali, start_vert)
    riempi_falda_con_linee(ax, sud, 'verticale', interasse_trapezoidali, start_vert)
    riempi_falda_con_linee(ax, est, 'orizzontale', interasse_triangolare, start_horiz)

    ax.set_aspect('equal')
    ax.set_title('Vista in pianta - Tetto a 3 falde')
    ax.set_xlabel('X (metri)')
    ax.set_ylabel('Y (metri)')
    ax.grid(True, linestyle='--', alpha=0.5)

    ax.text(0, metà_lato_corto + 1, 'NORD', ha='center', fontsize=12, weight='bold')
    ax.text(0, -metà_lato_corto - 1.2, 'SUD', ha='center', fontsize=12, weight='bold')

    ax.legend(loc='lower right', fontsize=9)
    plt.tight_layout()
    fig.savefig("tetto_3_falde_2D.png", dpi=300)

    plt.savefig("disegno2d_temp.png", dpi=300)

    plt.show()


# ✅ DISEGNO 3D PER TETTO A 3 FALDE

def disegna_tetto_3_falde_3d(lato_lungo, lato_corto, posizione_colmo, altezza_colmo,
                             interasse_trapezoidali, interasse_triangolare, taglio_tri):
    import plotly.graph_objects as go
    import os
    import webbrowser
    import numpy as np

    metà_lato_lungo = lato_lungo / 2
    metà_lato_corto = lato_corto / 2

    A = [-metà_lato_lungo, -metà_lato_corto, 0]
    B = [metà_lato_lungo, -metà_lato_corto, 0]
    C = [metà_lato_lungo, metà_lato_corto, 0]
    D = [-metà_lato_lungo, metà_lato_corto, 0]
    E = [-metà_lato_lungo, posizione_colmo, altezza_colmo]  # colmo inizio
    F = [metà_lato_lungo - taglio_tri, posizione_colmo, altezza_colmo]  # colmo fine

    vertices = np.array([A, B, C, D, E, F])
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]

    fig = go.Figure()

    # Mesh tetto
    faces = [
        [0, 1, 5], [0, 5, 4],  # Sud
        [3, 2, 5], [3, 5, 4],  # Nord
        [1, 2, 5],  # Est triangolare
    ]
    i, j, k = zip(*faces)

    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color='lightgray',
        opacity=1.0,
        flatshading=True,
        name='Tetto'
    ))

    fig.add_trace(go.Scatter3d(x=[E[0], F[0]], y=[E[1], F[1]], z=[E[2], F[2]],
                               mode='lines', line=dict(color='red', width=6), name='Colmo'))

    # Displuvi
    for p1, p2 in [(E, D), (E, A), (F, B), (F, C)]:
        fig.add_trace(go.Scatter3d(x=[p1[0], p2[0]], y=[p1[1], p2[1]], z=[p1[2], p2[2]],
                                   mode='lines', line=dict(color='blue', width=3), name='Displuvio'))

    # Righe
    falda_sud = [A, B, F, E]
    falda_nord = [D, C, F, E]
    falda_est = [B, C, F]

    riempi_falda_con_linee_3d(fig, falda_sud, 'verticale', interasse_trapezoidali)
    riempi_falda_con_linee_3d(fig, falda_nord, 'verticale', interasse_trapezoidali)
    riempi_falda_con_linee_3d(fig, falda_est, 'orizzontale', interasse=interasse_triangolare)

    fig.update_layout(
        title="Tetto 3D a 3 falde",
        scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z', aspectmode='data'),
        margin=dict(l=0, r=0, t=40, b=0)
    )

    fig.write_html("tetto_3_falde_3D.html")
    print("✅ Visualizzazione salvata in 'tetto_3_falde_3D.html'. Apri il file nel browser.")
    #webbrowser.open("file://" + os.path.abspath("tetto_3_falde_3D.html"))




#fine gestione tetto 3D

def riempi_falda_con_linee_3d(fig, polygon_3d, orientamento='verticale', interasse=0.6, colore='black'):
    """
    polygon_3d: lista di 3 o più punti [x, y, z]
    orientamento: 'verticale' = linee parallele all'asse Y (X fisso) | 'orizzontale' = linee parallele all'asse X (Y fisso)
    """
    from shapely.geometry import Polygon, LineString
    import numpy as np

    # Proietta il poligono su XY
    poly2d = Polygon([(x, y) for x, y, z in polygon_3d])
    xs, ys, zs = zip(*polygon_3d)

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Funzione per interpolare Z sul piano della falda
    def interp_z(x, y):
        p1, p2, p3 = polygon_3d[0], polygon_3d[1], polygon_3d[2]
        v1 = np.array(p2) - np.array(p1)
        v2 = np.array(p3) - np.array(p1)
        normal = np.cross(v1, v2)
        a, b, c = normal
        d = -np.dot(normal, p1)
        if c == 0:
            return 0
        z = -(a * x + b * y + d) / c
        return z

    step = interasse

    if orientamento == 'verticale':
        x_values = np.arange(min_x, max_x + step / 2, step)
        for x in x_values:
            line = LineString([(x, min_y), (x, max_y)])
            inter = line.intersection(poly2d)
            if inter.is_empty:
                continue
            if isinstance(inter, LineString):
                points = list(inter.coords)
            elif hasattr(inter, 'geoms'):
                points = []
                for g in inter.geoms:
                    points.extend(g.coords)
            else:
                continue

            for p1, p2 in zip(points[::2], points[1::2]):
                x1, y1 = p1
                x2, y2 = p2
                z1 = interp_z(x1, y1)
                z2 = interp_z(x2, y2)
                fig.add_trace(go.Scatter3d(
                    x=[x1, x2], y=[y1, y2], z=[z1, z2],
                    mode='lines',
                    line=dict(color=colore, width=1),
                    showlegend=False
                ))

    elif orientamento == 'orizzontale':
        y_values = np.arange(min_y, max_y + step / 2, step)
        for y in y_values:
            line = LineString([(min_x, y), (max_x, y)])
            inter = line.intersection(poly2d)
            if inter.is_empty:
                continue
            if isinstance(inter, LineString):
                points = list(inter.coords)
            elif hasattr(inter, 'geoms'):
                points = []
                for g in inter.geoms:
                    points.extend(g.coords)
            else:
                continue

            for p1, p2 in zip(points[::2], points[1::2]):
                x1, y1 = p1
                x2, y2 = p2
                z1 = interp_z(x1, y1)
                z2 = interp_z(x2, y2)
                fig.add_trace(go.Scatter3d(
                    x=[x1, x2], y=[y1, y2], z=[z1, z2],
                    mode='lines',
                    line=dict(color=colore, width=1),
                    showlegend=False
                ))



def altezza_falda(base_orizzontale, pendenza_gradi):
    pendenza_radianti = math.radians(pendenza_gradi)
    return math.tan(pendenza_radianti) * base_orizzontale


def chiedi_pendenza(nome_falda):
    while True:
        try:
            pendenza = float(input(f"Inserisci la pendenza della {nome_falda} (in gradi): "))
            return pendenza
        except ValueError:
            print("Input non valido. Inserisci un numero valido per la pendenza.")


def calcola_posizione_colmo(pendenza_sx, pendenza_dx, lato_corto):
    distanza = lato_corto / 2
    altezza_sx = math.tan(math.radians(pendenza_sx)) * distanza
    altezza_dx = math.tan(math.radians(pendenza_dx)) * distanza
    altezza_colmo = (altezza_sx + altezza_dx) / 2
    dx = altezza_colmo / math.tan(math.radians(pendenza_sx))
    dy = altezza_colmo / math.tan(math.radians(pendenza_dx))
    spostamento = (dy - dx) / 2
    return spostamento, altezza_colmo


def calcola_lunghezza_correntino(base_orizzontale, altezza_colmo):
    return math.sqrt(base_orizzontale ** 2 + altezza_colmo ** 2)


def calcola_correntini_falda_triangolare(nome_falda, lato_corto, altezza_colmo, taglio, interasse):
    print(f"\n--- Correntini per la falda {nome_falda.upper()} (triangolare) ---")

    correntini = []

    # Calcolo posizione del correntino principale (dove c'è il colmo)
    base_principale = taglio
    altezza_principale = altezza_colmo
    lunghezza_principale = math.sqrt(base_principale ** 2 + altezza_principale ** 2)
    correntini.append(("principale", 0.0, lunghezza_principale))
    print(f"Pos 0.00 m (colmo) | Lunghezza: {lunghezza_principale:.2f} m")

    # Verso destra
    print("\n[Triangolo lato destro]")
    distanza = 0
    while distanza < taglio:
        distanza += interasse
        if distanza >= taglio:
            break
        rapporto = (taglio - distanza) / taglio
        base = base_principale * rapporto
        altezza = altezza_principale * rapporto
        lunghezza = math.sqrt(base ** 2 + altezza ** 2)
        correntini.append(("triangolo_dx", distanza, lunghezza))
        print(f"Pos {distanza:.2f} m | Lunghezza: {lunghezza:.2f} m")

    # Verso sinistra
    print("\n[Triangolo lato sinistro]")
    distanza = 0
    while distanza < taglio:
        distanza += interasse
        if distanza >= taglio:
            break
        rapporto = (taglio - distanza) / taglio
        base = base_principale * rapporto
        altezza = altezza_principale * rapporto
        lunghezza = math.sqrt(base ** 2 + altezza ** 2)
        correntini.append(("triangolo_sx", -distanza, lunghezza))
        print(f"Pos -{distanza:.2f} m | Lunghezza: {lunghezza:.2f} m")

    return correntini


def riempi_falda_con_linee(ax, polygon, orientamento='verticale', interasse=0.6, start=0.0):
    xs, ys = zip(*polygon)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    path = Path(polygon)

    if orientamento == 'verticale':
        x = start + math.ceil((min_x - start) / interasse) * interasse
        while x <= max_x:
            clipped = [y for y in np.linspace(min_y, max_y, 200) if path.contains_point((x, y))]
            if clipped:
                ax.plot([x, x], [min(clipped), max(clipped)], 'm-', linewidth=0.8)
            x += interasse
    elif orientamento == 'orizzontale':
        y = start + math.ceil((min_y - start) / interasse) * interasse
        while y <= max_y:
            clipped = [x for x in np.linspace(min_x, max_x, 200) if path.contains_point((x, y))]
            if clipped:
                ax.plot([min(clipped), max(clipped)], [y, y], 'g-', linewidth=0.8)
            y += interasse


def disegna_tetto_completo(lato_lungo, lato_corto, posizione_colmo, altezza_colmo,
                           interasse_trapezoidali, interasse_triangolari, taglio_dx, taglio_sx):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 7))
    metà_lato_lungo = lato_lungo / 2
    metà_lato_corto = lato_corto / 2

    colmo_x_sx = - (lato_lungo / 2 - taglio_sx)
    colmo_x_dx = (lato_lungo / 2 - taglio_dx)
    colmo_y = posizione_colmo

    casa_x = [-metà_lato_lungo, metà_lato_lungo, metà_lato_lungo, -metà_lato_lungo, -metà_lato_lungo]
    casa_y = [-metà_lato_corto, -metà_lato_corto, metà_lato_corto, metà_lato_corto, -metà_lato_corto]
    ax.plot(casa_x, casa_y, 'k--', linewidth=1, label='Contorno casa')

    ax.plot([colmo_x_sx, colmo_x_dx], [colmo_y, colmo_y], 'r-', linewidth=2.5, label='Colmo')

    displuvi = [
        ((colmo_x_sx, colmo_y), (-metà_lato_lungo, metà_lato_corto)),
        ((colmo_x_sx, colmo_y), (-metà_lato_lungo, -metà_lato_corto)),
        ((colmo_x_dx, colmo_y), (metà_lato_lungo, metà_lato_corto)),
        ((colmo_x_dx, colmo_y), (metà_lato_lungo, -metà_lato_corto))
    ]

    for i, ((cx, cy), (ax_, ay_)) in enumerate(displuvi):
        label = 'Displuvio' if i == 0 else None
        ax.plot([cx, ax_], [cy, ay_], 'b-', linewidth=1.5, label=label)

    nord = [(colmo_x_sx, colmo_y), (colmo_x_dx, colmo_y),
            (metà_lato_lungo, metà_lato_corto), (-metà_lato_lungo, metà_lato_corto)]
    sud = [(colmo_x_sx, colmo_y), (colmo_x_dx, colmo_y),
           (metà_lato_lungo, -metà_lato_corto), (-metà_lato_lungo, -metà_lato_corto)]
    est = [(colmo_x_dx, colmo_y), (metà_lato_lungo, -metà_lato_corto), (metà_lato_lungo, metà_lato_corto)]
    ovest = [(colmo_x_sx, colmo_y), (-metà_lato_lungo, -metà_lato_corto), (-metà_lato_lungo, metà_lato_corto)]

    start_vert = - (lato_lungo - taglio_sx - taglio_dx) / 2
    start_horiz = posizione_colmo

    riempi_falda_con_linee(ax, nord, orientamento='verticale', interasse=interasse_trapezoidali, start=start_vert)
    riempi_falda_con_linee(ax, sud, orientamento='verticale', interasse=interasse_trapezoidali, start=start_vert)
    riempi_falda_con_linee(ax, est, orientamento='orizzontale', interasse=interasse_triangolari, start=start_horiz)
    riempi_falda_con_linee(ax, ovest, orientamento='orizzontale', interasse=interasse_triangolari, start=start_horiz)

    # Styling asse e griglia
    ax.set_aspect('equal')
    ax.set_title('Vista in pianta - Tetto a 4 falde', fontsize=14, weight='bold')
    ax.set_xlabel("X (metri)", fontsize=12)
    ax.set_ylabel("Y (metri)", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.5)

    # Limiti assi + margine
    buffer_x = lato_lungo * 0.1
    buffer_y = lato_corto * 0.1
    ax.set_xlim(-metà_lato_lungo - buffer_x, metà_lato_lungo + buffer_x)
    ax.set_ylim(-metà_lato_corto - buffer_y, metà_lato_corto + buffer_y)

    # Etichette cardinali
    ax.text(0, metà_lato_corto + buffer_y * 0.5, 'NORD', ha='center', fontsize=12, weight='bold')
    ax.text(0, -metà_lato_corto - buffer_y * 0.8, 'SUD', ha='center', fontsize=12, weight='bold')
    ax.text(metà_lato_lungo + buffer_x * 0.6, 0, 'OVEST', va='center', fontsize=12, weight='bold', rotation=90)
    ax.text(-metà_lato_lungo - buffer_x * 0.8, 0, 'EST', va='center', fontsize=12, weight='bold', rotation=90)

    # Legenda elegante
    ax.legend(loc='lower right', bbox_to_anchor=(1.0, -0.05), frameon=True, fontsize=10, ncol=3)

    plt.savefig("disegno2d_temp.png", dpi=300)

    plt.tight_layout()
    plt.show()


def suggerisci_interasse_ottimale(lunghezza_colmo, target=0.66, step=0.01, tolleranza=0.001):
    """
    Cerca l'interasse più vicino al target (es. 0.66) per cui la lunghezza del colmo è perfettamente divisibile.
    """
    migliori = []
    for i in np.arange(0.4, 1.0 + step, step):
        if abs((lunghezza_colmo / i) - round(lunghezza_colmo / i)) < tolleranza:
            migliori.append((i, abs(i - target)))
    if migliori:
        migliori.sort(key=lambda x: x[1])  # ordina per distanza dal target
        return round(migliori[0][0], 2)
    return round(target, 2)


def disegna_tetto_3d_plotly(lato_lungo, lato_corto, posizione_colmo, altezza_colmo,
                            interasse_trapezoidali, interasse_triangolari, taglio_dx, taglio_sx):
    metà_lato_lungo = lato_lungo / 2
    metà_lato_corto = lato_corto / 2

    colmo_x_sx = - (lato_lungo / 2 - taglio_sx)
    colmo_x_dx = (lato_lungo / 2 - taglio_dx)

    A = [-metà_lato_lungo, -metà_lato_corto, 0]
    B = [metà_lato_lungo, -metà_lato_corto, 0]
    C = [metà_lato_lungo, metà_lato_corto, 0]
    D = [-metà_lato_lungo, metà_lato_corto, 0]
    E = [colmo_x_sx, posizione_colmo, altezza_colmo]
    F = [colmo_x_dx, posizione_colmo, altezza_colmo]

    vertices = np.array([A, B, C, D, E, F])
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]

    faces = [
        [0, 1, 5], [0, 5, 4],
        [3, 2, 5], [3, 5, 4],
        [1, 2, 5],
        [0, 3, 4],
    ]
    i, j, k = zip(*faces)

    fig = go.Figure()

    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color='lightgray',
        opacity=1.0,
        flatshading=True,
        name='Tetto'
    ))

    # Colmo
    fig.add_trace(go.Scatter3d(
        x=[E[0], F[0]], y=[E[1], F[1]], z=[E[2], F[2]],
        mode='lines',
        line=dict(color='red', width=6),
        name='Colmo'
    ))

    # Displuvi
    displuvi = [(E, D), (E, A), (F, C), (F, B)]
    for p1, p2 in displuvi:
        fig.add_trace(go.Scatter3d(
            x=[p1[0], p2[0]], y=[p1[1], p2[1]], z=[p1[2], p2[2]],
            mode='lines',
            line=dict(color='blue', width=3),
            name='Displuvio'
        ))

    # --- Correntini / pattern sulle falde ---
    falda_sud = [
        A, B, [F[0], posizione_colmo, F[2]], [E[0], posizione_colmo, E[2]]
    ]
    falda_nord = [
        D, C, [F[0], posizione_colmo, F[2]], [E[0], posizione_colmo, E[2]]
    ]

    falda_est = [
        B, C, F
    ]
    falda_ovest = [
        A, D, E
    ]

    riempi_falda_con_linee_3d(fig, falda_sud, orientamento='verticale', interasse=interasse_trapezoidali,
                              colore='black')
    riempi_falda_con_linee_3d(fig, falda_nord, orientamento='verticale', interasse=interasse_trapezoidali,
                              colore='black')
    riempi_falda_con_linee_3d(fig, falda_est, orientamento='orizzontale', interasse=interasse_triangolari,
                              colore='green')
    riempi_falda_con_linee_3d(fig, falda_ovest, orientamento='orizzontale', interasse=interasse_triangolari,
                              colore='green')

    fig.update_layout(
        title="Tetto 3D a 4 falde con correntini",
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, t=40, b=0)
    )

    fig.write_html("tetto3D.html")
    print("✅ Visualizzazione salvata in 'tetto3D.html'. Apri il file nel browser.")
    fig.write_html("tetto3D.html")
    filepath = os.path.abspath("tetto3D.html")
    #webbrowser.open("file://" + filepath)








def calcola_correntini_falda_trapezoidale_L(
            nome_falda, lato_lungo, base_dx, base_sx, altezza_colmo,
            interasse, taglio_dx, taglio_sx, pendenza_trap, escludi_displuvio_est=False
    ):

    import math

    print(f"\n--- Correntini per la falda {nome_falda.upper()} (trapezoidale) ---")

    lunghezza_principale = altezza_colmo / math.sin(math.radians(pendenza_trap))

    lunghezza_rettangolo = lato_lungo - (base_dx + base_sx)
    num_correntini_rettangolo = int(lunghezza_rettangolo // interasse)
    limite = num_correntini_rettangolo + 1
    if escludi_displuvio_est:
        limite -= 1

    correntini = []

    print("\n[Rettangolo centrale]")
    for i in range(limite):
        posizione = base_dx + i * interasse
        correntini.append(("rettangolo", posizione, lunghezza_principale))
        print(f"Pos {posizione:.2f} m | Lunghezza: {lunghezza_principale:.2f} m")

    print("\n[Triangolo destro]")
    rapporto_dx = lunghezza_principale / base_dx
    distanza = base_dx
    while distanza > 0:
        distanza -= interasse
        if distanza <= 0:
            break
        nuova_base = distanza
        lunghezza = nuova_base * rapporto_dx
        correntini.append(("triangolo_dx", distanza, lunghezza))
        print(f"Pos {distanza:.2f} m | Lunghezza: {lunghezza:.2f} m")

    print("\n[Triangolo sinistro]")
    rapporto_sx = lunghezza_principale / base_sx
    distanza = base_sx
    while distanza > 0:
        distanza -= interasse
        if distanza <= 0:
            break
        nuova_base = distanza
        lunghezza = nuova_base * rapporto_sx
        correntini.append(("triangolo_sx", distanza, lunghezza))
        print(f"Pos {distanza:.2f} m | Lunghezza: {lunghezza:.2f} m")

    return correntini







def calcola_correntini_falda_parallelepipedale_L(nome_falda, lunghezza_rettangolo, base_dx, base_sx, altezza_colmo,
        interasse, pendenza_parall, escludi_displuvio_est=False
    ):

    import math

    print(lunghezza_rettangolo)
    print(base_sx)
    print(base_dx)
    print(altezza_colmo)
    print(pendenza_parall)


    print(f"\n--- Correntini per la falda {nome_falda.upper()} (parallelepipedale) ---")

    lunghezza_principale = altezza_colmo / math.sin(math.radians(pendenza_parall))
    print(lunghezza_principale)

    num_correntini_rettangolo = int(lunghezza_rettangolo // interasse)
    print(num_correntini_rettangolo)
    limite = num_correntini_rettangolo + 1
    if escludi_displuvio_est:
        limite -= 1

    correntini = []

    print("\n[Rettangolo centrale]")
    for i in range(limite):
        posizione = base_dx + i * interasse
        correntini.append(("rettangolo", posizione, lunghezza_principale))
        print(f"Pos {posizione:.2f} m | Lunghezza: {lunghezza_principale:.2f} m")

    print("\n[Triangolo destro]")
    rapporto_dx = lunghezza_principale / base_dx
    distanza = base_dx
    while distanza > 0:
        distanza -= interasse
        if distanza <= 0:
            break
        nuova_base = distanza
        lunghezza = nuova_base * rapporto_dx
        correntini.append(("triangolo_dx", distanza, lunghezza))
        print(f"Pos {distanza:.2f} m | Lunghezza: {lunghezza:.2f} m")

    print("\n[Triangolo sinistro]")
    rapporto_sx = lunghezza_principale / base_sx
    distanza = base_sx
    while distanza > 0:
        distanza -= interasse
        if distanza <= 0:
            break
        nuova_base = distanza
        lunghezza = nuova_base * rapporto_sx
        correntini.append(("triangolo_sx", distanza, lunghezza))
        print(f"Pos {distanza:.2f} m | Lunghezza: {lunghezza:.2f} m")

    return correntini














def calcola_correntini_falda_trapezoidale(
            nome_falda, lato_lungo, base_dx, base_sx, altezza_colmo,
            interasse, taglio_dx, taglio_sx, escludi_displuvio_est=False
    ):

    print(f"\n--- Correntini per la falda {nome_falda.upper()} (trapezoidale) ---")

    lunghezza_rettangolo = lato_lungo - (taglio_dx + taglio_sx)
    print(lunghezza_rettangolo)
    num_correntini_rettangolo = int(lunghezza_rettangolo // interasse)
    limite = num_correntini_rettangolo + 1
    if escludi_displuvio_est:
        limite -= 1  # Rimuove l'ultimo correntino che coinciderebbe con il displuvio

    correntini = []

    print("\n[Rettangolo centrale]")
    for i in range(limite):
        posizione = taglio_dx + i * interasse
        lunghezza = math.sqrt(base_dx ** 2 + altezza_colmo ** 2)
        correntini.append(("rettangolo", posizione, lunghezza))
        print(f"Pos {posizione:.2f} m | Lunghezza: {lunghezza:.2f} m")

    # Triangolo destro
    print("\n[Triangolo destro]")
    base_corrente = base_dx
    distanza = taglio_dx
    while distanza > 0:
        distanza -= interasse
        if distanza <= 0:
            break
        rapporto = max(distanza / taglio_dx, 0)
        base = base_dx * rapporto
        altezza = altezza_colmo * rapporto
        lunghezza = math.sqrt(base ** 2 + altezza ** 2)
        correntini.append(("triangolo_dx", distanza, lunghezza))
        print(f"Pos {distanza:.2f} m | Lunghezza: {lunghezza:.2f} m")

    # Triangolo sinistro
    print("\n[Triangolo sinistro]")
    base_corrente = base_sx
    distanza = taglio_sx
    while distanza > 0:
        distanza -= interasse
        if distanza <= 0:
            break
        rapporto = max(distanza / taglio_sx, 0)
        base = base_sx * rapporto
        altezza = altezza_colmo * rapporto
        lunghezza = math.sqrt(base ** 2 + altezza ** 2)
        correntini.append(("triangolo_sx", distanza, lunghezza))
        print(f"Pos {distanza:.2f} m | Lunghezza: {lunghezza:.2f} m")

    return correntini





def stampa_passafuori(nome_falda, correntini, lunghezza_passafuori):
    print(f"\n--- PASSAFUORI {nome_falda.upper()} ---")
    for _, posizione, _ in correntini:
        direzione = (
            "colmo" if posizione == 0 else f"{abs(posizione):.2f} m {'→ destra' if posizione > 0 else '← sinistra'}"
        )
        print(f"[{nome_falda.upper()}] Posizione: {direzione} | Lunghezza passafuori: {lunghezza_passafuori:.2f} m")







def main():


    print("Tipo di tetto:")
    print("1 - Tetto a due falde")
    print("2 - Tetto a quattro falde")
    print("3 - Tetto a tre falde")
    print("4 - Tetto monofalda")
    print("5 - Tetto a L")
    tipo_tetto = input("Seleziona il tipo di tetto (1, 2, 3, 4, 5): ")

    usa_rompitratta = False
    if tipo_tetto == "4":  # Solo per due falde o monofalda
        risposta = input("\nVuoi inserire un rompitratta? (s/N): ").strip().lower()
        usa_rompitratta = risposta == "s"

    usa_rompitratta_sx = False
    usa_rompitratta_dx = False

    if tipo_tetto == "1":  # Tetto a due falde
        print("\n--- ROMPITRATTA ---")
        risposta_sx = input("Vuoi inserire il rompitratta nella falda sinistra? (s/N): ").strip().lower()
        risposta_dx = input("Vuoi inserire il rompitratta nella falda destra?   (s/N): ").strip().lower()

        usa_rompitratta_sx = risposta_sx == "s"
        usa_rompitratta_dx = risposta_dx == "s"


    usa_tamponatura = False
    lunghezza_tamponatura = 0.0

    risposta = input("\nVuoi aggiungere la tamponatura lungo il cordolo perimetrale? (s/N): ").strip().lower()
    if risposta == "s":
        usa_tamponatura = True

    if tipo_tetto != "5":
        larghezza = float(input("Inserisci la larghezza della casa (in metri): "))
        lunghezza = float(input("Inserisci la lunghezza della casa (in metri): "))

        print("\n--- ORIENTAMENTO DEL COLMO ---")
        print("1 - Colmo lungo la **lunghezza** (es. 10x6 → colmo su 10 m)")
        print("2 - Colmo lungo la **larghezza** (es. 10x6 → colmo su 6 m)")
        scelta = input("Seleziona l'orientamento del colmo (1 o 2): ").strip()

        if scelta == "2":
            asse_colmo = "larghezza"
            lato_lungo = larghezza
            lato_corto = lunghezza
            orientamento_corto = "est-ovest"
        else:
            asse_colmo = "lunghezza"
            lato_lungo = lunghezza
            lato_corto = larghezza
            orientamento_corto = "nord-sud"


    #if tipo_tetto != "5":
      #  larghezza = float(input("Inserisci la larghezza della casa (in metri): "))
     #   lunghezza = float(input("Inserisci la lunghezza della casa (in metri): "))

    #    if lunghezza >= larghezza:
     #       asse_colmo = "lunghezza"
     #       lato_lungo = lunghezza
     #       lato_corto = larghezza
     #       orientamento_corto = "nord-sud"
     #   else:
      #      asse_colmo = "larghezza"
      #      lato_lungo = larghezza
      #      lato_corto = lunghezza
      #      orientamento_corto = "est-ovest"



        print("\n--- CONFIGURAZIONE SPORTO ---")
        sporto = float(input("Inserisci lo sporto desiderato (in metri): "))

        print("\nTipo di sporto:")
        print("1 - Classico (estensione del correntino)")
        print("2 - Passafuori")
        tipo_sporto = input("Seleziona il tipo di sporto (1 o 2): ").strip()


    if tipo_tetto == "1":
        print("\nInserisci la pendenza delle falde laterali (in gradi):")
        if orientamento_corto == "nord-sud":

            pendenza_sx = chiedi_pendenza("Falda Ovest (sinistra)")
            pendenza_dx = chiedi_pendenza("Falda Est (destra)")
        else:
            pendenza_sx = chiedi_pendenza("Falda Nord (sinistra)")
            pendenza_dx = chiedi_pendenza("Falda Sud (destra)")

        posizione_colmo, altezza_colmo = calcola_posizione_colmo(pendenza_sx, pendenza_dx, lato_corto)
        lunghezza_colmo = lato_lungo


        base_sx = (lato_corto / 2) - posizione_colmo
        base_dx = (lato_corto / 2) + posizione_colmo
        lunghezza_correntino_sx = calcola_lunghezza_correntino(base_sx, altezza_colmo)
        lunghezza_correntino_dx = calcola_lunghezza_correntino(base_dx, altezza_colmo)

        interasse_suggerito = suggerisci_interasse_ottimale(lato_lungo)



        print(f"\n[Consiglio] Interasse consigliato per falde: {interasse_suggerito:.2f} m")

        usa_default = input(f"Vuoi usare questo interasse ({interasse_suggerito:.2f} m)? (S/n): ").strip().lower()
        if usa_default == "n":
            try:
                interasse = float(input("Inserisci interasse personalizzato (in metri): "))
            except ValueError:
                print("Valore non valido. Uso quello consigliato.")
                interasse = interasse_suggerito
        else:
            interasse = interasse_suggerito

        num_correntini_per_falda = int(lato_lungo / interasse + 0.5) + 1
        totale_correntini = num_correntini_per_falda * 2

        correntini_falda_sx = [("rettangolo", i * interasse, lunghezza_correntino_sx) for i in
                               range(num_correntini_per_falda)]
        correntini_falda_dx = [("rettangolo", i * interasse, lunghezza_correntino_dx) for i in
                               range(num_correntini_per_falda)]

        if tipo_sporto == "1":
            allungamento_sx = calcola_allungamento_correntino(sporto, pendenza_sx)
            allungamento_dx = calcola_allungamento_correntino(sporto, pendenza_dx)
        else:
            allungamento_sx = allungamento_dx = 0.0

        lunghezza_effettiva_sx = lunghezza_correntino_sx + allungamento_sx
        lunghezza_effettiva_dx = lunghezza_correntino_dx + allungamento_dx



        print("\n--- Correntini per tetto a due falde ---")
        print(f"Falda sinistra: lunghezza correntino = {lunghezza_correntino_sx:.2f} m")
        print(f"Falda destra:   lunghezza correntino = {lunghezza_correntino_dx:.2f} m")
        print(f"Interasse: {interasse:.2f} m")
        print(f"Correntini per falda: {num_correntini_per_falda}")
        print(f"Totale correntini: {totale_correntini}")
        print(f"lunghezza effettiva correntini sx: {lunghezza_effettiva_sx}")
        print(f"lunghezza effettiva correntini dx: {lunghezza_effettiva_dx}")

        if tipo_sporto == "2":
            lunghezza_passafuori = moltiplicatore_sporto * sporto
            print(f"\n📏 Lunghezza standard passafuori: {lunghezza_passafuori:.2f} m")

            for i in range(num_correntini_per_falda):
                posizione = i * interasse
                print(f"[SX] Posizione: {posizione:.2f} m | Lunghezza passafuori: {lunghezza_passafuori:.2f} m")
                print(f"[DX] Posizione: {posizione:.2f} m | Lunghezza passafuori: {lunghezza_passafuori:.2f} m")


        if usa_rompitratta:
            altezza_rompitratta = altezza_colmo / 2
            print(f"\n🪵 Rompitratta attivo:")
            print(f" - Altezza dal piano base: {altezza_rompitratta:.2f} m")
            print(f" - Lunghezza (uguale al colmo): {lunghezza_colmo:.2f} m")

        perimetro = calcola_perimetro_rettangolare(lato_lungo, lato_corto)
        print(f"\n📐 Perimetro della casa: {perimetro:.2f} m")

        if usa_tamponatura:
            lunghezza_tamponatura = perimetro
            print(f"Lunghezza cordolo per tamponatura: {lunghezza_tamponatura} m")


        capriata_var = capriata(
            larghezza_casa=lato_corto,
            correntino_dx=lunghezza_correntino_dx,
            correntino_sx=lunghezza_correntino_sx,
            altezza_colmo=altezza_colmo,
            pendenza_dx=pendenza_dx,
            pendenza_sx=pendenza_sx,
            nome="Capriata"
        )

        disegna_tetto_due_falde_2d(lato_lungo, lato_corto, altezza_colmo, interasse, posizione_colmo,
                                   mostra_rompitratta_sx=usa_rompitratta_sx,
                                   mostra_rompitratta_dx=usa_rompitratta_dx)

        # ░▒▓█► AGGIUNTA COMPONENTI ALLA TABELLA ◄█▓▒░

        # Correntini con eventuale allungamento (per sporto classico)
        aggiungi_componenti("Correntino", "Correntino falda sinistra", correntini_falda_sx, allungamento_sx)
        aggiungi_componenti("Correntino", "Correntino falda destra", correntini_falda_dx, allungamento_dx)

        aggiungi_componenti("Colmo", "Colmo", [("lineare", 0, lunghezza_colmo)])


        # Tamponatura (solo se richiesta)
        if usa_tamponatura:
            aggiungi_componenti("Tamponatura", "Tamponatura esterna", [("lineare", 0, perimetro)])

        # Passafuori (solo se tipo sporto == 2)
        if tipo_sporto == "2":
            lunghezza_passafuori = moltiplicatore_sporto * sporto
            lista_passafuori = []

            for falda, lista in [
                ("Sinistra", correntini_falda_sx),
                ("Destra", correntini_falda_dx)
            ]:
                for _, posizione, _ in lista:
                    lista_passafuori.append((falda, posizione, lunghezza_passafuori))

            aggiungi_componenti("Passafuori", "Passafuori esterni", lista_passafuori)

        aggiungi_componenti("Puntone", "Puntone Capriata", [e for e in capriata_var if e[0] == "Puntone"])

        aggiungi_componenti("Catena", "Catena Capriata", [e for e in capriata_var if e[0] == "Catena"])

        aggiungi_componenti("Monaco", "Monaco Capriata", [e for e in capriata_var if e[0] == "Monaco"])

        aggiungi_componenti("Saetta", "Saetta Capriata", [e for e in capriata_var if e[0] == "Saetta"])

        # ► Stampa finale
        print("\n📦 Tabella componenti generata:")
        global tabella_componenti
        tabella_componenti = completa_tabella_componenti(tabella_componenti)
        print(tabella_componenti)
        # dopo tutte le chiamate a aggiungi_componenti:
        df = pd.DataFrame(tabella_componenti)
        # salva CSV o Excel
        df.to_csv("tabella_componenti.csv", index=False)
        df.to_excel("tabella_componenti.xlsx", index=False)
        print("File salvati: tabella_componenti.csv e .xlsx")

        dati_preventivo = chiedi_dati_preventivo()


        genera_report_completo(
            nome_file_pdf="report_preventivo.pdf",
            tabella_componenti=tabella_componenti,
            path_logo="Logo_Cavanna_Strutture.png",  # <-- nome corretto
            path_disegno="disegno2d_temp.png",
            dati_preventivo=dati_preventivo
        )

        os.remove("disegno2d_temp.png")

        disegna_tetto_due_falde_3d(lato_lungo, lato_corto, altezza_colmo, interasse, posizione_colmo,
                                   mostra_rompitratta_sx=usa_rompitratta_sx,
                                   mostra_rompitratta_dx=usa_rompitratta_dx, pendenza_sx = pendenza_sx, pendenza_dx = pendenza_dx)




    elif tipo_tetto == "2":
        print("\nInserisci la pendenza delle 4 falde (in gradi):")
        if orientamento_corto == "nord-sud":
            # lato corto = N-S → TRIANGOLARI: Nord/Sud ; TRAPEZOIDALI: Est/Ovest
            p_tri_sx = chiedi_pendenza("Falda Nord (triangolare, lato corto)")
            p_tri_dx = chiedi_pendenza("Falda Sud  (triangolare, lato corto)")
            p_trap_sx = chiedi_pendenza("Falda Est  (trapezoidale, lato lungo)")
            p_trap_dx = chiedi_pendenza("Falda Ovest (trapezoidale, lato lungo)")
        else:
            # lato corto = E-O → TRIANGOLARI: Est/Ovest ; TRAPEZOIDALI: Nord/Sud
            p_tri_sx = chiedi_pendenza("Falda Est  (triangolare, lato corto)")
            p_tri_dx = chiedi_pendenza("Falda Ovest (triangolare, lato corto)")
            p_trap_sx = chiedi_pendenza("Falda Nord (trapezoidale, lato lungo)")
            p_trap_dx = chiedi_pendenza("Falda Sud  (trapezoidale, lato lungo)")

        print("lunghezza lato corto")
        print(lato_corto)

        # 1) Altezza colmo (sempre dalle TRAPEZOIDALI sul lato CORTO)
        posizione_colmo, altezza_colmo = calcola_posizione_colmo(p_trap_sx, p_trap_dx, lato_corto)

        # 2) Tagli del colmo (dalle TRIANGOLARI)
        taglio_sx = altezza_colmo / math.tan(math.radians(p_tri_sx))
        taglio_dx = altezza_colmo / math.tan(math.radians(p_tri_dx))

        # 3) Lunghezza colmo con guardia
        lunghezza_colmo = lato_lungo - (taglio_sx + taglio_dx)

        print(f"[DEBUG] lato_lungo={lato_lungo}, lato_corto={lato_corto}, orientamento_corto={orientamento_corto}")
        print(f"[DEBUG] altezza_colmo={altezza_colmo:.3f}")
        print(f"[DEBUG] taglio_sx={taglio_sx:.3f}, taglio_dx={taglio_dx:.3f}, somma={taglio_sx + taglio_dx:.3f}")

        colmo_uguale_zero = False

        if lunghezza_colmo <= 0:
            print("\n❌ Il tetto così NON chiude bene per questo orientamento: colmo ≤ 0 (piramidale).")
            if lato_lungo > 0 and altezza_colmo > 0:
                # Angolo minimo per TRIANGOLARI UGUALI che rende il colmo > 0:
                # 2*h/tan(phi) < lato_lungo  →  tan(phi) > 2*h/lato_lungo  →  phi_min = atan(2*h/lato_lungo)
                phi_min = math.degrees(math.atan((2 * altezza_colmo) / lato_lungo))
                print(f"   🔧 Suggerimento: imposta le due TRIANGOLARI a ≥ {phi_min:.1f}°.")
                scelta = input(
                    f"\nVuoi procedere impostando entrambe le triangolari a {phi_min:.1f}°? (S/n): ").strip().lower()

                if scelta == "s":
                    # Aggiorna le triangolari (senza abbassarle se fossero già più grandi)
                    p_tri_sx = max(p_tri_sx, phi_min)
                    p_tri_dx = max(p_tri_dx, phi_min)

                    # Ricalcola con i nuovi angoli
                    taglio_sx = altezza_colmo / math.tan(math.radians(p_tri_sx))
                    taglio_dx = altezza_colmo / math.tan(math.radians(p_tri_dx))
                    lunghezza_colmo = lato_lungo - (taglio_sx + taglio_dx)

                    if lunghezza_colmo == 0:
                        colmo_uguale_zero = True

                    print(
                        f"✅ Triangolari aggiornate a ≥ {phi_min:.1f}°. Nuova lunghezza colmo: {lunghezza_colmo:.2f} m")
                    print(
                        f"[DEBUG] taglio_sx={taglio_sx:.3f}, taglio_dx={taglio_dx:.3f}, somma={taglio_sx + taglio_dx:.3f}")

                    if lunghezza_colmo < 0:
                        print(
                            "⚠️ Anche così il colmo resta ≤ 0. Valuta di ridurre le trapezoidali o cambiare orientamento.\n")
                        return
                    # altrimenti prosegui normalmente…
                else:
                    print("Interruzione configurazione tetto a quattro falde.\n")
                    return
            else:
                return




        interasse_trapezio_suggerito = suggerisci_interasse_ottimale(lunghezza_colmo)
        print(f"\n[Consiglio] Interasse consigliato per falde trapezoidali (colmo lungo {lunghezza_colmo:.2f} m): {interasse_trapezio_suggerito:.2f} m")

        usa_default = input(f"\n✅ Interasse consigliato per falde trapezoidali: {interasse_trapezio_suggerito:.2f} m. Vuoi usarlo? (S/n): ").strip().lower()
        if usa_default == "n":
            try:
                interasse_trapezoidali = float(input("Inserisci interasse personalizzato per le falde trapezoidali (Nord/Sud): "))
            except ValueError:
                print("Valore non valido. Uso quello consigliato.")
                interasse_trapezoidali = interasse_trapezio_suggerito
        else:
            interasse_trapezoidali = interasse_trapezio_suggerito

        usa_stesso = input(f"\nVuoi usare lo stesso interasse ({interasse_trapezoidali:.2f} m) anche per le falde triangolari (Est/Ovest)? (S/n): ").strip().lower()
        if usa_stesso == "n":
            try:
                interasse_triangolari = float(input("Inserisci interasse per le falde triangolari (Est/Ovest): "))
            except ValueError:
                interasse_triangolari = interasse_trapezoidali
        else:
            interasse_triangolari = interasse_trapezoidali

        base_sud_dx = (lato_corto / 2) + posizione_colmo
        base_sud_sx = (lato_corto / 2) + posizione_colmo
        base_nord_dx = (lato_corto / 2) - posizione_colmo
        base_nord_sx = (lato_corto / 2) - posizione_colmo

        correntini_falda_sud = calcola_correntini_falda_trapezoidale("Sud", lato_lungo, base_sud_dx, base_sud_sx, altezza_colmo, interasse_trapezoidali, taglio_dx, taglio_sx)
        correntini_falda_nord = calcola_correntini_falda_trapezoidale("Nord", lato_lungo, base_nord_sx, base_nord_dx, altezza_colmo, interasse_trapezoidali, taglio_sx, taglio_dx)

        # Per la falda EST
        base_est_sx = (lato_corto / 2) + posizione_colmo
        base_est_dx = (lato_corto / 2) - posizione_colmo
        correntini_falda_est = calcola_correntini_falda_triangolare_L(
            "Est", base_est_sx, base_est_dx, altezza_colmo, interasse_triangolari, taglio_dx
        )

        # Per la falda OVEST
        base_ovest_sx = (lato_corto / 2) - posizione_colmo
        base_ovest_dx = (lato_corto / 2) + posizione_colmo
        correntini_falda_ovest = calcola_correntini_falda_triangolare_L(
            "Ovest", base_ovest_sx, base_ovest_dx, altezza_colmo, interasse_triangolari, taglio_sx
        )

        H_est = math.sqrt(taglio_dx ** 2 + altezza_colmo ** 2)
        H_ovest = math.sqrt(taglio_sx ** 2 + altezza_colmo ** 2)

        metà_lato_corto = lato_corto / 2

        B_est_dx = metà_lato_corto + posizione_colmo
        B_est_sx = metà_lato_corto - posizione_colmo

        B_ovest_dx = metà_lato_corto - posizione_colmo
        B_ovest_sx = metà_lato_corto + posizione_colmo

        displuvio_est_dx = math.sqrt(H_est ** 2 + B_est_dx ** 2)
        displuvio_est_sx = math.sqrt(H_est ** 2 + B_est_sx ** 2)

        displuvio_ovest_dx = math.sqrt(H_ovest ** 2 + B_ovest_dx ** 2)
        displuvio_ovest_sx = math.sqrt(H_ovest ** 2 + B_ovest_sx ** 2)


        print("\n--- Correntini finali per falda EST (triangolare) ---")
        for tipo, posizione, lunghezza in correntini_falda_est:
            direzione = "colmo" if posizione == 0 else f"{abs(posizione):.2f} m {'a destra' if posizione > 0 else 'a sinistra'}"
            print(f"Pos {direzione} | Lunghezza: {lunghezza:.2f} m")

        print("\n--- Correntini finali per falda OVEST (triangolare) ---")
        for tipo, posizione, lunghezza in correntini_falda_ovest:
            direzione = "colmo" if posizione == 0 else f"{abs(posizione):.2f} m {'a destra' if posizione > 0 else 'a sinistra'}"
            print(f"Pos {direzione} | Lunghezza: {lunghezza:.2f} m")

        if tipo_sporto == "1":
            all_trap_sx = calcola_allungamento_correntino(sporto, p_trap_sx)
            all_trap_dx = calcola_allungamento_correntino(sporto, p_trap_dx)
            all_tri_sx = calcola_allungamento_correntino(sporto, p_tri_sx)
            all_tri_dx = calcola_allungamento_correntino(sporto, p_trap_dx)
        else:
            all_trap_sx = all_trap_dx = all_tri_sx = all_tri_dx = 0.0

        for tipo, posizione, lunghezza in correntini_falda_est:
            lunghezza_finale = lunghezza + all_tri_dx
            print(f"[EST] Pos {posizione:.2f} m | Base: {lunghezza:.2f} m → Totale: {lunghezza_finale:.2f} m")
        for tipo, posizione, lunghezza in correntini_falda_ovest:
            lunghezza_finale = lunghezza + all_tri_sx
            print(f"[OVEST] Pos {posizione:.2f} m | Base: {lunghezza:.2f} m → Totale: {lunghezza_finale:.2f} m")
        for tipo, posizione, lunghezza in correntini_falda_sud:
            lunghezza_finale = lunghezza + all_trap_dx
            print(f"[SUD] Pos {posizione:.2f} m | Base: {lunghezza:.2f} m → Totale: {lunghezza_finale:.2f} m")
        for tipo, posizione, lunghezza in correntini_falda_nord:
            lunghezza_finale = lunghezza + all_trap_sx
            print(f"[NORD] Pos {posizione:.2f} m | Base: {lunghezza:.2f} m → Totale: {lunghezza_finale:.2f} m")

        if tipo_sporto == "2":
            lunghezza_passafuori = moltiplicatore_sporto * sporto
            print(f"\n📏 Lunghezza standard passafuori: {lunghezza_passafuori:.2f} m")

            for tipo, posizione, _ in correntini_falda_est:
                print(f"[EST] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")
            for tipo, posizione, _ in correntini_falda_ovest:
                print(f"[OVEST] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")
            for tipo, posizione, _ in correntini_falda_sud:
                print(f"[SUD] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")
            for tipo, posizione, _ in correntini_falda_nord:
                print(f"[NORD] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")

        print("\n--- Lunghezze displuvi (colmo → angoli casa) ---")
        print(f"Displuvio EST destro  (verso Sud-Est):  {displuvio_est_dx:.2f} m")
        print(f"Displuvio EST sinistro (verso Nord-Est): {displuvio_est_sx:.2f} m")
        print(f"Displuvio OVEST destro  (verso Sud-Ovest):  {displuvio_ovest_dx:.2f} m")
        print(f"Displuvio OVEST sinistro (verso Nord-Ovest): {displuvio_ovest_sx:.2f} m")

        perimetro = calcola_perimetro_rettangolare(lato_lungo, lato_corto)
        print(f"\n📐 Perimetro della casa: {perimetro:.2f} m")

        if usa_tamponatura:
            lunghezza_tamponatura = perimetro
            print(f"Lunghezza cordolo per tamponatura: {lunghezza_tamponatura} m")

        lunghezza_correntino_rett_dx = next(
            (lunghezza for tipo, _, lunghezza in correntini_falda_nord if tipo == "rettangolo"),
            None
        )

        lunghezza_correntino_rett_sx = next(
            (lunghezza for tipo, _, lunghezza in correntini_falda_sud if tipo == "rettangolo"),
            None
        )


        if colmo_uguale_zero == False:
            capriata_var = capriata(
                larghezza_casa=lato_corto,
                correntino_dx=lunghezza_correntino_rett_dx,
                correntino_sx=lunghezza_correntino_rett_sx,
                altezza_colmo=altezza_colmo,
                pendenza_dx=p_trap_dx,
                pendenza_sx=p_trap_sx,
                nome="Capriata"
            )
            capriata_control = "si"






        disegna_tetto_completo(lato_lungo, lato_corto, posizione_colmo, altezza_colmo, interasse_trapezoidali,
                               interasse_triangolari, taglio_dx, taglio_sx)

        # ░▒▓█► AGGIUNTA COMPONENTI ALLA TABELLA ◄█▓▒░

        # Correntini con eventuale allungamento (per sporto classico)
        aggiungi_componenti("Correntino", "Correntino triangolare Ovest", correntini_falda_ovest, all_tri_dx)
        aggiungi_componenti("Correntino", "Correntino triangolare EST", correntini_falda_est, all_tri_sx)
        aggiungi_componenti("Correntino", "Correntino trapezoidale NORD", correntini_falda_nord, all_trap_dx)
        aggiungi_componenti("Correntino", "Correntino trapezoidale SUD", correntini_falda_sud, all_trap_sx)


        aggiungi_componenti("Colmo", "Colmo", [("lineare", 0, lunghezza_colmo)])


        aggiungi_componenti("Displuvio", "Displuvio nord-ovest", [("lineare", 0, displuvio_est_sx)])
        aggiungi_componenti("Displuvio", "Displuvio nord-est", [("lineare", 0, displuvio_est_dx)])
        aggiungi_componenti("Displuvio", "Displuvio sud-est", [("lineare", 0, displuvio_ovest_dx)])
        aggiungi_componenti("Displuvio", "Displuvio sud-ovest", [("lineare", 0, displuvio_ovest_sx)])

        # Tamponatura (solo se richiesta)
        if usa_tamponatura:
            aggiungi_componenti("Tamponatura", "Tamponatura esterna", [("lineare", 0, perimetro)])

        # Passafuori (solo se tipo sporto == 2)
        if tipo_sporto == "2":
            lunghezza_passafuori = moltiplicatore_sporto * sporto
            lista_passafuori = []

            for falda, lista in [
            ("Est", correntini_falda_est),
            ("Ovest", correntini_falda_ovest),
            ("Sud", correntini_falda_sud),
            ("Nord", correntini_falda_nord)
            ]:
                for _, posizione, _ in lista:
                    lista_passafuori.append((falda, posizione, lunghezza_passafuori))

            aggiungi_componenti("Passafuori", "Passafuori esterni", lista_passafuori)

        if capriata_control == "si":


            aggiungi_componenti("Puntone", "Puntone Capriata", [e for e in capriata_var if e[0] == "Puntone"])

            aggiungi_componenti("Catena", "Catena Capriata", [e for e in capriata_var if e[0] == "Catena"])


            aggiungi_componenti("Monaco", "Monaco Capriata", [e for e in capriata_var if e[0] == "Monaco"])


            aggiungi_componenti("Saetta", "Saetta Capriata", [e for e in capriata_var if e[0] == "Saetta"])


        # ► Stampa finale
        print("\n📦 Tabella componenti generata:")

        tabella_componenti = completa_tabella_componenti(tabella_componenti)
        print(tabella_componenti)
        # dopo tutte le chiamate a aggiungi_componenti:
        df = pd.DataFrame(tabella_componenti)
        # salva CSV o Excel
        df.to_csv("tabella_componenti.csv", index=False)
        df.to_excel("tabella_componenti.xlsx", index=False)
        print("File salvati: tabella_componenti.csv e .xlsx")

        dati_preventivo = chiedi_dati_preventivo()


        genera_report_completo(
            nome_file_pdf="report_preventivo.pdf",
            tabella_componenti=tabella_componenti,
            path_logo="Logo_Cavanna_Strutture.png",  # <-- nome corretto
            path_disegno="disegno2d_temp.png",
            dati_preventivo=dati_preventivo
        )

        os.remove("disegno2d_temp.png")


        disegna_tetto_3d_plotly(lato_lungo, lato_corto, posizione_colmo, altezza_colmo, interasse_trapezoidali,
                                interasse_triangolari, taglio_dx, taglio_sx)



    elif tipo_tetto == "3":
        gestisci_tetto_tre_falde(lato_lungo, lato_corto, sporto, tipo_sporto,usa_tamponatura, orientamento_corto)
        return


    elif tipo_tetto == "4":
        print("\n--- CONFIGURAZIONE TETTO A MONOFALDA ---")

        pendenza = chiedi_pendenza("Falda monofalda (inclinata verso Nord/Sud)")

        # Altezza colmo = tan(pendenza) * lato corto
        altezza_colmo = altezza_falda(lato_corto, pendenza)
        lunghezza_colmo = lato_lungo
        posizione_colmo = 0  # è centrato orizzontalmente per disegno

        # Suggerisci interasse
        interasse_suggerito = suggerisci_interasse_ottimale(lunghezza_colmo)
        print(f"\n[Consiglio] Interasse consigliato: {interasse_suggerito:.2f} m")

        usa_default = input("Vuoi usare questo interasse? (S/n): ").strip().lower()
        if usa_default == "n":
            try:
                interasse = float(input("Inserisci interasse personalizzato (in metri): "))
            except ValueError:
                print("Valore non valido. Uso quello consigliato.")
                interasse = interasse_suggerito
        else:
            interasse = interasse_suggerito

        lunghezza_correntino = math.sqrt(lato_corto ** 2 + altezza_colmo ** 2)
        num_correntini = int(lato_lungo / interasse + 0.5) + 1

        correntini_falda = []

        for i in range(num_correntini):
            posizione = i * interasse
            correntini_falda.append(("rettangolo", posizione, lunghezza_correntino))



        lunghezza_correntino_non_allungato = lunghezza_correntino

        if tipo_sporto == "1":
            allungamento = calcola_allungamento_correntino(sporto, pendenza)
            lunghezza_correntino += allungamento
        else:
            allungamento = 0.0


        print("\n--- RISULTATI ---")
        print("Tipo di tetto: monofalda (1 falda inclinata)")
        print(f"La falda pende verso: {'Sud' if orientamento_corto == 'nord-sud' else 'Ovest'}")
        print(f"Lunghezza del colmo (tutto il lato lungo): {lunghezza_colmo:.2f} m")
        print(f"Altezza del colmo: {altezza_colmo:.2f} m")
        print(f"lunghezza correntino senza sporto: {lunghezza_correntino_non_allungato:.2f} m")
        print(f"Lunghezza tipica di ogni correntino: {lunghezza_correntino:.2f} m")
        print(f"Allungamento dovuto allo sporto: {allungamento:.2f} m")
        print(f"Numero totale di correntini: {num_correntini}")
        print(f"Interasse tra i correntini: {interasse:.2f} m")

        if tipo_sporto == "2":
            lunghezza_passafuori = moltiplicatore_sporto * sporto
            print(f"\n📏 Passafuori (monofalda): lunghezza = {lunghezza_passafuori:.2f} m")

            for i in range(num_correntini):
                posizione = i * interasse
                print(f"[MONO] Pos: {posizione:.2f} m | Passafuori: {lunghezza_passafuori:.2f} m")

        if usa_rompitratta:
            altezza_rompitratta = altezza_colmo / 2
            print(f"\n🪵 Rompitratta attivo:")
            print(f" - Altezza dal piano base: {altezza_rompitratta:.2f} m")
            print(f" - Lunghezza (uguale al colmo): {lunghezza_colmo:.2f} m")

        perimetro = calcola_perimetro_rettangolare(lato_lungo, lato_corto)
        print(f"\n📐 Perimetro della casa: {perimetro:.2f} m")

        if usa_tamponatura:
            lunghezza_tamponatura = perimetro
            print(f"Lunghezza cordolo per tamponatura: {lunghezza_tamponatura} m")



        # Disegni
        disegna_tetto_monofalda_2d(lato_lungo, lato_corto, altezza_colmo, orientamento_corto, mostra_rompitratta=usa_rompitratta)

        # ░▒▓█► AGGIUNTA COMPONENTI ALLA TABELLA ◄█▓▒░

        # Correntini con eventuale allungamento (per sporto classico)
        aggiungi_componenti("Correntino", "Correntino Falda", correntini_falda, allungamento)

        if usa_rompitratta:
            aggiungi_componenti("Rompitratta", "Rompitratta monofalda", [("lineare", 0, lunghezza_colmo)])


        # Tamponatura (solo se richiesta)
        if usa_tamponatura:
            aggiungi_componenti("Tamponatura", "Tamponatura esterna", [("lineare", 0, perimetro)])

        # Passafuori (solo se tipo sporto == 2)
        if tipo_sporto == "2":
            lunghezza_passafuori = moltiplicatore_sporto * sporto
            lista_passafuori = []

            for falda, lista in [
                ("falda", correntini_falda),

            ]:
                for _, posizione, _ in lista:
                    lista_passafuori.append((falda, posizione, lunghezza_passafuori))

            aggiungi_componenti("Passafuori", "Passafuori esterni", lista_passafuori)


        # ► Stampa finale
        print("\n📦 Tabella componenti generata:")

        tabella_componenti = completa_tabella_componenti(tabella_componenti)
        print(tabella_componenti)
        # dopo tutte le chiamate a aggiungi_componenti:
        df = pd.DataFrame(tabella_componenti)
        # salva CSV o Excel
        df.to_csv("tabella_componenti.csv", index=False)
        df.to_excel("tabella_componenti.xlsx", index=False)
        print("File salvati: tabella_componenti.csv e .xlsx")

        dati_preventivo = chiedi_dati_preventivo()


        genera_report_completo(
            nome_file_pdf="report_preventivo.pdf",
            tabella_componenti=tabella_componenti,
            path_logo="Logo_Cavanna_Strutture.png",  # <-- nome corretto
            path_disegno="disegno2d_temp.png",
            dati_preventivo=dati_preventivo
        )

        os.remove("disegno2d_temp.png")





        disegna_tetto_monofalda_3d(lato_lungo, lato_corto, altezza_colmo, interasse, verso="nord", mostra_rompitratta=usa_rompitratta)



    elif tipo_tetto == "5":
        gestisci_tetto_L(usa_tamponatura)
        return


    # Output posizione colmo
    if posizione_colmo == 0:
        print("Il colmo è esattamente al centro della casa.")
    else:
        spostamento_valore = abs(posizione_colmo)
        direzione = "destra" if posizione_colmo < 0 else "sinistra"
        print(f"Posizione del colmo: {spostamento_valore:.2f} m a {direzione} del centro.")

    # Output generico
    print("\n--- RISULTATI ---")
    print(f"Tipo di tetto: {'2 falde' if tipo_tetto == '1' else '4 falde'}")
    print(f"La trave di colmo è lungo l'asse della {asse_colmo}.")
    print(f"Lunghezza della trave di colmo: {lunghezza_colmo:.2f} m")
    print(f"Altezza della trave di colmo dal piano base: {altezza_colmo:.2f} m")

if __name__ == "__main__":
    main()





# app.py
# Streamlit GUI wrapper for your existing computational engine in main.py
# NOTE: this does NOT change your logic; it orchestrates inputs/outputs via UI
# and uses your functions as-is wherever possible.

import io
import os
import math
import contextlib
from typing import Dict, Tuple, List

import streamlit as st
import pandas as pd

import plotly.graph_objects as go
import plotly.io as pio
# Disabilita l'apertura in nuove finestre: soppianta Figure.show()
def _no_show(self, *args, **kwargs):
    return None
try:
    go.Figure.show = _no_show  # evita popup esterni
    pio.renderers.default = "json"  # evita renderer "browser"
except Exception:
    pass

# Import your core logic
import main as core

st.set_page_config(
    page_title="Calcolo Tetti - GUI",
    page_icon="🏠",
    layout="wide",
)

# Widen content area so the 3D can appear bigger
st.markdown(
    "<style>.block-container{max-width:1600px !important;}</style>",
    unsafe_allow_html=True
)


# ---------- Helpers ----------

COMP_COLS = ["n", "nome", "tag", "lunghezza", "larghezza", "altezza", "volume_m3", "costo_euro"]

def init_state():
    if "tabella_componenti" not in st.session_state:
        st.session_state.tabella_componenti = pd.DataFrame(columns=COMP_COLS)
    if "log" not in st.session_state:
        st.session_state.log = ""
    if "preventivo" not in st.session_state:
        st.session_state.preventivo = {"Nome Cliente":"", "Progetto":"", "Numero":"", "Cantiere":""}
    if "last_disegno2d" not in st.session_state:
        st.session_state.last_disegno2d = None
    if "selected_tipo" not in st.session_state:
        st.session_state.selected_tipo = None
    if "current_3d_html" not in st.session_state:
        st.session_state.current_3d_html = None
    if "viewer_height" not in st.session_state:
        st.session_state.viewer_height = 1100

def log_prints(fn, *args, **kwargs) -> Tuple[str, any]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = fn(*args, **kwargs)
    return buf.getvalue(), out

def sync_core_df_from_state():
    # Keep your module's global DF in sync with session state
    core.tabella_componenti = st.session_state.tabella_componenti.copy()

def sync_state_df_from_core():
    st.session_state.tabella_componenti = core.tabella_componenti.copy()

def add_components(tag: str, nome: str, lista: List[Tuple[str, float, float]], allungamento: float = 0.0):
    """Use your existing function to add rows to the global table."""
    sync_core_df_from_state()
    _ = core.aggiungi_componenti(tag, nome, lista, allungamento=allungamento)
    sync_state_df_from_core()

def finalize_costs_ui(df: pd.DataFrame):
    """Interactive completion of sections and costs, identical math to your CLI."""
    st.subheader("Sezioni e costi")
    tags = list(df["tag"].dropna().unique())
    if not tags:
        st.info("⚠️ Aggiungi prima dei componenti (correntini, colmo, ecc.).")
        return df

    cols = st.columns(3)
    sezioni: Dict[str, Tuple[float,float]] = {}
    costo_m3_map: Dict[str, float] = {}

    with st.form("comp_form"):
        for tag in tags:
            c1, c2, c3 = st.columns([1,1,1])
            larg_cm = c1.number_input(f"Larghezza {tag} (cm)", min_value=0.0, value=10.0, step=0.5, key=f"larg_{tag}")
            alt_cm  = c2.number_input(f"Altezza {tag} (cm)",   min_value=0.0, value=10.0, step=0.5, key=f"alt_{tag}")
            costo_m3 = c3.number_input(f"Costo €/m³ {tag}", min_value=0.0, value=450.0, step=10.0, key=f"costo_{tag}")
            sezioni[tag] = (larg_cm/100.0, alt_cm/100.0)  # converti in metri
            costo_m3_map[tag] = costo_m3

        submitted = st.form_submit_button("Applica sezioni e costi")
        if submitted:
            df = df.copy()
            for i, row in df.iterrows():
                tag = row["tag"]
                lunghezza = row["lunghezza"] or 0.0
                larg, alt = sezioni.get(tag, (0.0, 0.0))
                volume = (larg * alt) * lunghezza
                costo  = volume * costo_m3_map.get(tag, 0.0)
                df.at[i, "larghezza"] = larg
                df.at[i, "altezza"]   = alt
                df.at[i, "volume_m3"] = volume
                df.at[i, "costo_euro"] = costo

            # Riga totale
            costo_totale = float(df["costo_euro"].fillna(0.0).sum())
            df.loc[len(df)] = [""] * len(df.columns)
            df.loc[len(df)] = ["", "TOTALE", "", "", "", "", "", costo_totale]
            st.session_state.tabella_componenti = df
            st.success(f"💸 Costo totale componenti: € {costo_totale:,.2f}")
            st.rerun()

    return st.session_state.tabella_componenti

def download_buttons(df: pd.DataFrame):
    if df.empty:
        return
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Scarica CSV", csv, file_name="tabella_componenti.csv", mime="text/csv")
    with io.BytesIO() as bio:
        try:
            # Write Excel with pandas (xlsxwriter/openpyxl not guaranteed in env; fall back to CSV when unavailable)
            df.to_excel(bio, index=False)
            bio.seek(0)
            st.download_button("⬇️ Scarica Excel", bio.getvalue(), file_name="tabella_componenti.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception:
            st.caption("Per l'Excel potrebbe servire `openpyxl`. È comunque disponibile il CSV.")

def show_plotly_html(path: str, height: int = 520, width: int = 1600):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        # iframe della component con larghezza esplicita
        st.components.v1.html(html, height=height, width=width, scrolling=True)
    else:
        st.info("Nessun 3D generato ancora.")

def calcola_capriata_elementi(
    n_capriate: int,
    larghezza_casa: float,
    correntino_dx: float,
    correntino_sx: float,
    altezza_colmo: float,
    pendenza_dx: float,
    pendenza_sx: float,
) -> List[Tuple[str, float, float]]:
    """Replica della logica di core.capriata() ma senza input(), parametrizzata per la UI."""
    elementi = []
    monaco = altezza_colmo - 0.20
    saetta_destra = monaco / math.sin(math.radians(pendenza_sx)) if pendenza_sx != 0 else 0.0
    saetta_sinistra = monaco / math.sin(math.radians(pendenza_dx)) if pendenza_dx != 0 else 0.0
    for _ in range(n_capriate):
        elementi.extend([
            ("Puntone", 0, correntino_dx),
            ("Puntone", 0, correntino_sx),
            ("Catena", 0, larghezza_casa),
            ("Monaco", 0, monaco),
            ("Saetta", 0, saetta_destra),
            ("Saetta", 0, saetta_sinistra),
        ])
    return elementi

# ---------- Sidebar (preventivo + opzioni globali) ----------

init_state()
with st.sidebar:
    st.header("📋 Dati Preventivo")
    st.session_state.preventivo["Nome Cliente"] = st.text_input("Nome cliente", st.session_state.preventivo["Nome Cliente"])
    st.session_state.preventivo["Progetto"] = st.text_input("Nome progetto", st.session_state.preventivo["Progetto"])
    st.session_state.preventivo["Numero"] = st.text_input("Numero (telefono o riferimento)", st.session_state.preventivo["Numero"])
    st.session_state.preventivo["Cantiere"] = st.text_input("Cantiere", st.session_state.preventivo["Cantiere"])
    # Il logo resta fisso dal progetto (Logo_Cavanna_Strutture.png). Le immagini extra si caricano nella scheda Report.
    st.markdown("---")
    st.caption("Suggerimento: dopo ogni calcolo, vai nella scheda **Componenti & Costi** per impostare sezioni e costi e generare il PDF.")

st.title("Quotation System")
st.write("Scegli il **tipo di tetto** e inserisci i parametri. L'app aggiungerà automaticamente i componenti alla tabella e ti permetterà di generare report e disegni 2D/3D.")

tab_calc, tab_comp, tab_draw, tab_report = st.tabs(["⚙️ Calcolo", "📦 Componenti & Costi", "🖼️ Disegni", "🧾 Report PDF"])

# ---------- CALCOLO ----------
with tab_calc:
    tipo = st.selectbox("Tipo di tetto", ["2 falde", "4 falde", "3 falde", "Monofalda", "A forma di L"])

    if tipo != "A forma di L":
        c1, c2 = st.columns(2)
        larghezza = c1.number_input("Larghezza casa (m)", min_value=0.1, value=6.0, step=0.1)
        lunghezza = c2.number_input("Lunghezza casa (m)", min_value=0.1, value=10.0, step=0.1)

        st.subheader("Orientamento colmo")
        orient_choice = st.radio("Il colmo è parallelo a…", ["Lunghezza (es. 10x6 → colmo su 10 m)", "Larghezza (es. 10x6 → colmo su 6 m)"], index=0)
        if orient_choice.startswith("Larghezza"):
            asse_colmo = "larghezza"
            lato_lungo = larghezza
            lato_corto = lunghezza
            orientamento_corto = "est-ovest"
        else:
            asse_colmo = "lunghezza"
            lato_lungo = lunghezza
            lato_corto = larghezza
            orientamento_corto = "nord-sud"

        st.subheader("Sporo e altre opzioni")
        c1, c2, c3 = st.columns(3)
        sporto = c1.number_input("Sporo desiderato (m)", min_value=0.0, value=0.3, step=0.05)
        tipo_sporto = c2.selectbox("Tipo di sporto", ["Classico (estensione correntino)", "Passafuori"])
        usa_tamponatura = c3.checkbox("Aggiungi tamponatura lungo il cordolo perimetrale", value=False)
        if tipo == "2 falde":
            c4, c5 = st.columns(2)
            usa_rompitratta_sx = c4.checkbox("Rompitratta falda sinistra", value=False)
            usa_rompitratta_dx = c5.checkbox("Rompitratta falda destra", value=False)
        else:
            usa_rompitratta_sx = usa_rompitratta_dx = False

        # ------------- TETTO A DUE FALDE -------------
    if tipo == "2 falde":
        st.subheader("Pendenze falde")
        if orientamento_corto == "nord-sud":
            pendenza_sx = st.number_input("Falda Ovest (sinistra) [°]", min_value=0.0, value=19.0, step=0.5)
            pendenza_dx = st.number_input("Falda Est (destra) [°]", min_value=0.0, value=19.0, step=0.5)
        else:
            pendenza_sx = st.number_input("Falda Nord (sinistra) [°]", min_value=0.0, value=19.0, step=0.5)
            pendenza_dx = st.number_input("Falda Sud (destra) [°]", min_value=0.0, value=19.0, step=0.5)

        # Calcoli
        posizione_colmo, altezza_colmo = core.calcola_posizione_colmo(pendenza_sx, pendenza_dx, lato_corto)
        lunghezza_colmo = lato_lungo
        base_sx = (lato_corto / 2) - posizione_colmo
        base_dx = (lato_corto / 2) + posizione_colmo
        lunghezza_correntino_sx = core.calcola_lunghezza_correntino(base_sx, altezza_colmo)
        lunghezza_correntino_dx = core.calcola_lunghezza_correntino(base_dx, altezza_colmo)

        # Interasse suggerito
        interasse_suggerito = core.suggerisci_interasse_ottimale(lunghezza_colmo)
        interasse = st.number_input("Interasse correntini (m)", min_value=0.1, value=float(interasse_suggerito), step=0.01)

        # Pulsanti
        colA, colB, colC = st.columns([1,1,1])
        calcola2f = colA.button("🧮 Calcola disegni (2 falde)")

        n_capriate = colC.number_input("Capriate", min_value=0, step=1, value=0, help="Numero capriate da aggiungere")
        add_cap2f = colC.button("➕ Aggiungi capriate")

        if calcola2f:
            _ = core.disegna_tetto_due_falde_2d(lato_lungo, lato_corto, altezza_colmo, interasse, posizione_colmo,
                                                mostra_rompitratta_sx=usa_rompitratta_sx, mostra_rompitratta_dx=usa_rompitratta_dx)
            st.session_state.last_disegno2d = "disegno2d_temp.png"
            _ = core.disegna_tetto_due_falde_3d(lato_lungo, lato_corto, altezza_colmo, interasse, posizione_colmo,
                                               mostra_rompitratta_sx=usa_rompitratta_sx, mostra_rompitratta_dx=usa_rompitratta_dx,
                                               pendenza_sx=pendenza_sx, pendenza_dx=pendenza_dx)
            st.session_state.selected_tipo = "2 falde"
            st.session_state.current_3d_html = "tetto_due_falde_3D.html"
            st.success("Disegni aggiornati.")

                        # liste correntini
            num_correntini_per_falda = int(lato_lungo / interasse + 0.5) + 1
            correntini_falda_sx = [("rettangolo", i*interasse, lunghezza_correntino_sx) for i in range(num_correntini_per_falda)]
            correntini_falda_dx = [("rettangolo", i*interasse, lunghezza_correntino_dx) for i in range(num_correntini_per_falda)]

            if tipo_sporto.startswith("Classico"):
                all_sx = core.calcola_allungamento_correntino(sporto, pendenza_sx)
                all_dx = core.calcola_allungamento_correntino(sporto, pendenza_dx)
            else:
                all_sx = all_dx = 0.0

            # Disegno 2D
            _ = core.disegna_tetto_due_falde_2d(lato_lungo, lato_corto, altezza_colmo, interasse, posizione_colmo,
                                                mostra_rompitratta_sx=usa_rompitratta_sx, mostra_rompitratta_dx=usa_rompitratta_dx)
            st.session_state.last_disegno2d = "disegno2d_temp.png"

            # Aggiunte
            add_components("Correntino", "Correntino falda sinistra", correntini_falda_sx, all_sx)
            add_components("Correntino", "Correntino falda destra", correntini_falda_dx, all_dx)
            add_components("Colmo", "Colmo", [("lineare", 0, lunghezza_colmo)])

            # Tamponatura
            if usa_tamponatura:
                perimetro = core.calcola_perimetro_rettangolare(lato_lungo, lato_corto)
                add_components("Tamponatura", "Tamponatura esterna", [("lineare", 0, perimetro)])

            # Passafuori
            if tipo_sporto.startswith("Passafuori"):
                lunghezza_passafuori = core.moltiplicatore_sporto * sporto
                lista_passafuori = []
                for _, pos, _ in correntini_falda_sx + correntini_falda_dx:
                    lista_passafuori.append(("Passafuori", pos, lunghezza_passafuori))
                add_components("Passafuori", "Passafuori esterni", lista_passafuori)

            
                # Rompitratta 2 falde nei componenti
                if usa_rompitratta_sx:
                    add_components("Rompitratta", "Rompitratta falda sinistra", [("lineare", 0, lato_lungo)])
                if usa_rompitratta_dx:
                    add_components("Rompitratta", "Rompitratta falda destra",   [("lineare", 0, lato_lungo)])
# Capriate (aggiunte con pulsante dedicato)
            pass

            st.success("Componenti aggiunti per tetto **a due falde**.")
            st.rerun()
        if n_capriate>0:
            cap_elems = calcola_capriata_elementi(int(n_capriate), lato_corto, lunghezza_correntino_dx, lunghezza_correntino_sx,
                                                  altezza_colmo, pendenza_dx, pendenza_sx)
            add_components("Puntone", "Puntone Capriata", [e for e in cap_elems if e[0] == "Puntone"])
            add_components("Catena", "Catena Capriata", [e for e in cap_elems if e[0] == "Catena"])
            add_components("Monaco", "Monaco Capriata", [e for e in cap_elems if e[0] == "Monaco"])
            add_components("Saetta", "Saetta Capriata", [e for e in cap_elems if e[0] == "Saetta"])
            st.success(f"Capriate aggiunte: {int(n_capriate)}")
            st.rerun()

    # ------------- TETTO A QUATTRO FALDE -------------
    if tipo == "4 falde":
        
        # Evita NameError prima di calcolare
        correntini_falda_sud = []
        correntini_falda_nord = []
        correntini_falda_est = []
        correntini_falda_ovest = []
        st.subheader("Pendenze falde (triangolari sul lato corto, trapezoidali sul lato lungo)")
        if orientamento_corto == "nord-sud":
            # Triangolari: Nord/Sud ; Trapezoidali: Est/Ovest
            p_tri_sx = st.number_input("Falda Nord (triangolare) [°]", min_value=0.0, value=19.0, step=0.5)
            p_tri_dx = st.number_input("Falda Sud  (triangolare) [°]", min_value=0.0, value=19.0, step=0.5)
            p_trap_sx = st.number_input("Falda Est  (trapezoidale) [°]", min_value=0.0, value=19.0, step=0.5)
            p_trap_dx = st.number_input("Falda Ovest (trapezoidale) [°]", min_value=0.0, value=19.0, step=0.5)
        else:
            # Triangolari: Est/Ovest ; Trapezoidali: Nord/Sud
            p_tri_sx = st.number_input("Falda Est  (triangolare) [°]", min_value=0.0, value=19.0, step=0.5)
            p_tri_dx = st.number_input("Falda Ovest (triangolare) [°]", min_value=0.0, value=19.0, step=0.5)
            p_trap_sx = st.number_input("Falda Nord (trapezoidale) [°]", min_value=0.0, value=19.0, step=0.5)
            p_trap_dx = st.number_input("Falda Sud  (trapezoidale) [°]", min_value=0.0, value=19.0, step=0.5)

        # 1) Altezza colmo dalle trapezoidali sul lato corto
        posizione_colmo, altezza_colmo = core.calcola_posizione_colmo(p_trap_sx, p_trap_dx, lato_corto)

        # 2) Tagli del colmo (dalle triangolari)
        taglio_sx = altezza_colmo / math.tan(math.radians(p_tri_sx)) if p_tri_sx != 0 else 0.0
        taglio_dx = altezza_colmo / math.tan(math.radians(p_tri_dx)) if p_tri_dx != 0 else 0.0

        lunghezza_colmo = lato_lungo - (taglio_sx + taglio_dx)
        if lunghezza_colmo <= 0:
            st.error("❌ Con le pendenze attuali il **colmo ≤ 0** (scompare). Aumenta le triangolari o riduci quelle trapezoidali.")
        interasse_trap = core.suggerisci_interasse_ottimale(max(lunghezza_colmo, 0.01))
        interasse_tri = interasse_trap  # default uguale
        c1, c2 = st.columns(2)
        interasse_trap = c1.number_input("Interasse falde trapezoidali (m)", min_value=0.1, value=float(interasse_trap), step=0.01)
        interasse_tri = c2.number_input("Interasse falde triangolari (m)", min_value=0.1, value=float(interasse_tri), step=0.01)

        colA4, colB4, colC4 = st.columns([1,1,1])
        calcola4f = colA4.button("🧮 Calcola disegni (4 falde)")

        n_capriate4 = colC4.number_input("Capriate", min_value=0, step=1, value=0, key="capriate_4")
        add_cap4f = colC4.button("➕ Aggiungi capriate (4f)")
        if calcola4f:
            _ = core.disegna_tetto_3d_plotly(lato_lungo, lato_corto, posizione_colmo, altezza_colmo,
                                             interasse_trap, interasse_tri, taglio_dx, taglio_sx)
            st.session_state.last_disegno2d = "disegno2d_temp.png"
            st.session_state.selected_tipo = "4 falde"
            st.session_state.current_3d_html = "tetto3D.html"
            st.success("Disegni aggiornati.")

            # Correntini trapezoidali NORD/SUD (asse colmo lungo lato lungo)
            correntini_falda_sud = core.calcola_correntini_falda_trapezoidale(
                "Sud", lato_lungo, (lato_corto/2)+posizione_colmo, (lato_corto/2)-posizione_colmo, altezza_colmo,
                interasse_trap, taglio_dx, taglio_sx
            )
            correntini_falda_nord = core.calcola_correntini_falda_trapezoidale(
                "Nord", lato_lungo, (lato_corto/2)-posizione_colmo, (lato_corto/2)+posizione_colmo, altezza_colmo,
                interasse_trap, taglio_sx, taglio_dx
            )
            # Correntini triangolari EST/OVEST
            correntini_falda_est = core.calcola_correntini_falda_triangolare_L(
                "Est", (lato_corto/2)+posizione_colmo, (lato_corto/2)-posizione_colmo, altezza_colmo, interasse_tri, taglio_dx
            )
            correntini_falda_ovest = core.calcola_correntini_falda_triangolare_L(
                "Ovest", (lato_corto/2)-posizione_colmo, (lato_corto/2)+posizione_colmo, altezza_colmo, interasse_tri, taglio_sx
            )

            # Allungamenti per sporto classico
            if tipo_sporto.startswith("Classico"):
                all_trap_sx = core.calcola_allungamento_correntino(sporto, p_trap_sx)
                all_trap_dx = core.calcola_allungamento_correntino(sporto, p_trap_dx)
                all_tri_sx = core.calcola_allungamento_correntino(sporto, p_tri_sx)
                all_tri_dx = core.calcola_allungamento_correntino(sporto, p_tri_dx)
            else:
                all_trap_sx = all_trap_dx = all_tri_sx = all_tri_dx = 0.0

            # Disegno 2D & 3D
            _ = core.disegna_tetto_completo(lato_lungo, lato_corto, posizione_colmo, altezza_colmo,
                                            interasse_trap, interasse_tri, taglio_dx, taglio_sx)
            st.session_state.last_disegno2d = "disegno2d_temp.png"
            _ = core.disegna_tetto_3d_plotly(lato_lungo, lato_corto, posizione_colmo, altezza_colmo,
                                             interasse_trap, interasse_tri, taglio_dx, taglio_sx)

            add_components("Correntino", "Correntino triangolare Ovest", correntini_falda_ovest, all_tri_dx)
            add_components("Correntino", "Correntino triangolare Est", correntini_falda_est,  all_tri_sx)
            add_components("Correntino", "Correntino trapezoidale Nord", correntini_falda_nord, all_trap_dx)
            add_components("Correntino", "Correntino trapezoidale Sud",  correntini_falda_sud,  all_trap_sx)
            add_components("Colmo", "Colmo", [("lineare", 0, lunghezza_colmo)])

            # Displuvi (stesse formule dell'engine)
            H_est = math.sqrt(taglio_dx**2 + altezza_colmo**2)
            H_ovest = math.sqrt(taglio_sx**2 + altezza_colmo**2)
            metà = lato_corto/2
            B_est_dx = metà + posizione_colmo
            B_est_sx = metà - posizione_colmo
            B_ovest_dx = metà - posizione_colmo
            B_ovest_sx = metà + posizione_colmo
            displuvio_est_dx = math.sqrt(H_est**2 + B_est_dx**2)
            displuvio_est_sx = math.sqrt(H_est**2 + B_est_sx**2)
            displuvio_ovest_dx = math.sqrt(H_ovest**2 + B_ovest_dx**2)
            displuvio_ovest_sx = math.sqrt(H_ovest**2 + B_ovest_sx**2)
            add_components("Displuvio", "Displuvio nord-est",   [("lineare", 0, displuvio_est_dx)])
            add_components("Displuvio", "Displuvio sud-est",    [("lineare", 0, displuvio_est_sx)])
            add_components("Displuvio", "Displuvio sud-ovest",  [("lineare", 0, displuvio_ovest_dx)])
            add_components("Displuvio", "Displuvio nord-ovest", [("lineare", 0, displuvio_ovest_sx)])

            # Tamponatura
            if usa_tamponatura:
                perimetro = core.calcola_perimetro_rettangolare(lato_lungo, lato_corto)
                add_components("Tamponatura", "Tamponatura esterna", [("lineare", 0, perimetro)])

            # Passafuori
            if tipo_sporto.startswith("Passafuori"):
                lunghezza_passafuori = core.moltiplicatore_sporto * sporto
                lista = []
                for _, pos, _ in (correntini_falda_est + correntini_falda_ovest + correntini_falda_nord + correntini_falda_sud):
                    lista.append(("Passafuori", pos, lunghezza_passafuori))
                add_components("Passafuori", "Passafuori esterni", lista)

            # Capriate
            n_capriate = st.number_input("Quante capriate? (4 falde)", min_value=1, step=1, value=3, key="cap_4")
            # Per la capriata usiamo le lunghezze dei correntini "trapezoidali" come puntone
            # Scegliamo il caso peggiore (base maggiore) per sicurezza
            corr_dx = max([l for _,_,l in correntini_falda_sud] + [0.0])
            corr_sx = max([l for _,_,l in correntini_falda_nord] + [0.0])
            cap_elems = calcola_capriata_elementi(n_capriate, lato_corto, corr_dx, corr_sx, altezza_colmo, p_trap_dx, p_trap_sx)
            add_components("Puntone", "Puntone Capriata", [e for e in cap_elems if e[0] == "Puntone"])
            add_components("Catena", "Catena Capriata", [e for e in cap_elems if e[0] == "Catena"])
            add_components("Monaco", "Monaco Capriata", [e for e in cap_elems if e[0] == "Monaco"])
            add_components("Saetta", "Saetta Capriata", [e for e in cap_elems if e[0] == "Saetta"])

            st.success("Componenti aggiunti per tetto **a quattro falde**.")
            st.rerun()
        if n_capriate4>0:
            corr_dx = max([l for _,_,l in correntini_falda_sud] + [0.0])
            corr_sx = max([l for _,_,l in correntini_falda_nord] + [0.0])
            cap_elems = calcola_capriata_elementi(int(n_capriate4), lato_corto, corr_dx, corr_sx, altezza_colmo, p_trap_dx, p_trap_sx)
            add_components("Puntone", "Puntone Capriata", [e for e in cap_elems if e[0] == "Puntone"])
            add_components("Catena", "Catena Capriata", [e for e in cap_elems if e[0] == "Catena"])
            add_components("Monaco", "Monaco Capriata", [e for e in cap_elems if e[0] == "Monaco"])
            add_components("Saetta", "Saetta Capriata", [e for e in cap_elems if e[0] == "Saetta"])
            st.success(f"Capriate aggiunte: {int(n_capriate4)}")
            st.rerun()

        # ------------- TETTO A 3 FALDE -------------
    if tipo == "3 falde":
        
        # Evita NameError prima di calcolare
        correntini_nord = []
        correntini_sud = []
        correntini_tri = []
        st.subheader("Lato corto con falda triangolare")
        lato_tri = st.selectbox("Dove sta la falda triangolare sul lato corto?", ["Nord", "Sud"] if orientamento_corto=="nord-sud" else ["Est", "Ovest"])
        # Etichette coerenti con l'engine
        if orientamento_corto == "nord-sud":
            label_tri = f"Falda triangolare ({lato_tri})"
            label_trap_sx = "Falda trapezoidale sinistra (Est)"
            label_trap_dx = "Falda trapezoidale destra (Ovest)"
        else:
            label_tri = f"Falda triangolare ({lato_tri})"
            label_trap_sx = "Falda trapezoidale sinistra (Nord)"
            label_trap_dx = "Falda trapezoidale destra (Sud)"

        st.subheader("Pendenze")
        pendenza_tri = st.number_input(f"{label_tri} [°]", min_value=0.0, value=19.0, step=0.5)
        pendenza_trap_sx = st.number_input(f"{label_trap_sx} [°]", min_value=0.0, value=19.0, step=0.5)
        pendenza_trap_dx = st.number_input(f"{label_trap_dx} [°]", min_value=0.0, value=19.0, step=0.5)

        # Altezza colmo da trapezoidali
        posizione_colmo, altezza_colmo = core.calcola_posizione_colmo(pendenza_trap_sx, pendenza_trap_dx, lato_corto)
        # Taglio solo su una estremità (triangolare)
        taglio_tri = altezza_colmo / math.tan(math.radians(pendenza_tri)) if pendenza_tri != 0 else 0.0
        lunghezza_colmo = lato_lungo - taglio_tri

        interasse_trap = core.suggerisci_interasse_ottimale(max(lunghezza_colmo, 0.01))
        interasse_tri = interasse_trap
        c1, c2 = st.columns(2)
        interasse_trap = c1.number_input("Interasse falde trapezoidali (m)", min_value=0.1, value=float(interasse_trap), step=0.01, key="i3a")
        interasse_tri = c2.number_input("Interasse falde triangolari (m)", min_value=0.1, value=float(interasse_tri), step=0.01, key="i3b")

        colA3, colB3, colC3 = st.columns([1,1,1])
        calcola3f = colA3.button("🧮 Calcola disegni (3 falde)")

        n_capriate3 = colC3.number_input("Capriate", min_value=0, step=1, value=0, key="capriate_3")
        add_cap3f = colC3.button("➕ Aggiungi capriate (3f)")
        if calcola3f:
            _ = core.disegna_tetto_3_falde_2d(lato_lungo, lato_corto, posizione_colmo, altezza_colmo, interasse_trap, interasse_tri, taglio_tri)
            st.session_state.last_disegno2d = "disegno2d_temp.png"
            _ = core.disegna_tetto_3_falde_3d(lato_lungo, lato_corto, posizione_colmo, altezza_colmo, interasse_trap, interasse_tri, taglio_tri)
            st.session_state.selected_tipo = "3 falde"
            st.session_state.current_3d_html = "tetto_3_falde_3D.html"
            st.success("Disegni aggiornati.")

            # Correnti trapezoidali: due lati lunghi
            correntini_nord = core.calcola_correntini_falda_trapezoidale(
                "Nord", lato_lungo, (lato_corto/2)-posizione_colmo, (lato_corto/2)+posizione_colmo, altezza_colmo,
                interasse_trap, taglio_sx=0.0, taglio_dx=taglio_tri  # ipotesi: colmo tagliato verso lato triangolare
            )
            correntini_sud = core.calcola_correntini_falda_trapezoidale(
                "Sud", lato_lungo, (lato_corto/2)+posizione_colmo, (lato_corto/2)-posizione_colmo, altezza_colmo,
                interasse_trap, taglio_sx=taglio_tri, taglio_dx=0.0
            )

            # Triangolare su lato corto selezionato
            if orientamento_corto == "nord-sud":
                if lato_tri.lower() == "nord":
                    base_sx = (lato_corto/2) - posizione_colmo
                    base_dx = (lato_corto/2) + posizione_colmo
                else:  # sud
                    base_sx = (lato_corto/2) + posizione_colmo
                    base_dx = (lato_corto/2) - posizione_colmo
            else:
                if lato_tri.lower() == "est":
                    base_sx = (lato_corto/2) + posizione_colmo
                    base_dx = (lato_corto/2) - posizione_colmo
                else:  # ovest
                    base_sx = (lato_corto/2) - posizione_colmo
                    base_dx = (lato_corto/2) + posizione_colmo

            correntini_tri = core.calcola_correntini_falda_triangolare_L("Triangolare", base_sx, base_dx, altezza_colmo, interasse_tri, taglio_tri)

            # Allungamenti per sporto classico
            if tipo_sporto.startswith("Classico"):
                all_tri = core.calcola_allungamento_correntino(sporto, pendenza_tri)
                all_trap_sx = core.calcola_allungamento_correntino(sporto, pendenza_trap_sx)
                all_trap_dx = core.calcola_allungamento_correntino(sporto, pendenza_trap_dx)
            else:
                all_tri = all_trap_sx = all_trap_dx = 0.0

            # Disegni
            _ = core.disegna_tetto_3_falde_2d(lato_lungo, lato_corto, posizione_colmo, altezza_colmo, interasse_trap, interasse_tri, taglio_tri)
            st.session_state.last_disegno2d = "disegno2d_temp.png"
            _ = core.disegna_tetto_3_falde_3d(lato_lungo, lato_corto, posizione_colmo, altezza_colmo, taglio_tri, interasse_trap)

            # Componenti
            add_components("Correntino", "Correntino triangolare", correntini_tri, all_tri)
            add_components("Correntino", "Correntino trapezoidale nord", correntini_nord, all_trap_dx)
            add_components("Correntino", "Correntino trapezoidale sud",  correntini_sud,  all_trap_sx)
            add_components("Colmo", "Colmo", [("lineare", 0, lunghezza_colmo)])

            # Tamponatura
            if usa_tamponatura:
                perimetro = core.calcola_perimetro_rettangolare(lato_lungo, lato_corto)
                add_components("Tamponatura", "Tamponatura esterna", [("lineare", 0, perimetro)])

            # Passafuori
            if tipo_sporto.startswith("Passafuori"):
                lunghezza_passafuori = core.moltiplicatore_sporto * sporto
                lista = []
                for _, pos, _ in (correntini_tri + correntini_nord + correntini_sud):
                    lista.append(("Passafuori", pos, lunghezza_passafuori))
                add_components("Passafuori", "Passafuori esterni", lista)

            # Capriate
            n_capriate = st.number_input("Quante capriate? (3 falde)", min_value=1, step=1, value=3, key="cap_3")
            corr_ref_dx = max([l for _,_,l in correntini_sud] + [0.0])
            corr_ref_sx = max([l for _,_,l in correntini_nord] + [0.0])
            cap_elems = calcola_capriata_elementi(n_capriate, lato_corto, corr_ref_dx, corr_ref_sx, altezza_colmo, pendenza_trap_dx, pendenza_trap_sx)
            add_components("Puntone", "Puntone Capriata", [e for e in cap_elems if e[0] == "Puntone"])
            add_components("Catena", "Catena Capriata", [e for e in cap_elems if e[0] == "Catena"])
            add_components("Monaco", "Monaco Capriata", [e for e in cap_elems if e[0] == "Monaco"])
            add_components("Saetta", "Saetta Capriata", [e for e in cap_elems if e[0] == "Saetta"])

            st.success("Componenti aggiunti per tetto **a 3 falde**.")
            st.rerun()
        if n_capriate3>0:
            corr_ref_dx = max([l for _,_,l in correntini_sud] + [0.0])
            corr_ref_sx = max([l for _,_,l in correntini_nord] + [0.0])
            cap_elems = calcola_capriata_elementi(int(n_capriate3), lato_corto, corr_ref_dx, corr_ref_sx, altezza_colmo, pendenza_trap_dx, pendenza_trap_sx)
            add_components("Puntone", "Puntone Capriata", [e for e in cap_elems if e[0] == "Puntone"])
            add_components("Catena", "Catena Capriata", [e for e in cap_elems if e[0] == "Catena"])
            add_components("Monaco", "Monaco Capriata", [e for e in cap_elems if e[0] == "Monaco"])
            add_components("Saetta", "Saetta Capriata", [e for e in cap_elems if e[0] == "Saetta"])
            st.success(f"Capriate aggiunte: {int(n_capriate3)}")
            st.rerun()

        # ------------- TETTO MONOFALDA -------------
    if tipo == "Monofalda":
        pendenza = st.number_input("Pendenza monofalda [°]", min_value=0.0, value=19.0, step=0.5)
        
        usa_rompitratta_mono = st.checkbox("Rompitratta", value=False)
        # Altezza colmo = tan(pendenza) * (lato_corto/2)? L'engine usa altezza_falda(lato_corto, pendenza)
        altezza_colmo = core.altezza_falda(lato_corto, pendenza)
        posizione_colmo = 0.0
        interasse = core.suggerisci_interasse_ottimale(lato_lungo)
        interasse = st.number_input("Interasse correntini (m)", min_value=0.1, value=float(interasse), step=0.01)

        colAm, colBm = st.columns([1,1])
        calcolam = colAm.button("🧮 Calcola disegni (monofalda)")

        if calcolam:
            _ = core.disegna_tetto_monofalda_2d(lato_lungo, lato_corto, altezza_colmo, orientamento_corto, mostra_rompitratta=usa_rompitratta_mono)
            st.session_state.last_disegno2d = "disegno2d_temp.png"
            _ = core.disegna_tetto_monofalda_3d(lato_lungo, lato_corto, altezza_colmo, interasse, mostra_rompitratta=usa_rompitratta_mono)
            st.session_state.selected_tipo = "Monofalda"
            st.session_state.current_3d_html = "tetto_monofalda_3d.html"
            st.success("Disegni aggiornati.")

            # Disegni
            _ = core.disegna_tetto_monofalda_2d(lato_lungo, lato_corto, altezza_colmo, orientamento_corto, mostra_rompitratta=usa_rompitratta_mono)
            st.session_state.last_disegno2d = "disegno2d_temp.png"
            _ = core.disegna_tetto_monofalda_3d(lato_lungo, lato_corto, altezza_colmo, interasse, mostra_rompitratta=usa_rompitratta_mono)

            # Correntini: su lato lungo, tutti uguali
            num_correntini = int(lato_lungo / interasse + 0.5) + 1
            lunghezza_corr = core.calcola_lunghezza_correntino(lato_corto, altezza_colmo)
            correntini = [("monofalda", i*interasse, lunghezza_corr) for i in range(num_correntini)]
            if tipo_sporto.startswith("Classico"):
                allung = core.calcola_allungamento_correntino(sporto, pendenza)
            else:
                allung = 0.0

            add_components("Correntino", "Correntino monofalda", correntini, allung)
            
            if usa_rompitratta_mono:
                add_components("Rompitratta", "Rompitratta monofalda", [("lineare", 0, lato_lungo)])
        # Monofalda: nessun colmo (ma possiamo lasciare fuori)
            if usa_tamponatura:
                perimetro = core.calcola_perimetro_rettangolare(lato_lungo, lato_corto)
                add_components("Tamponatura", "Tamponatura esterna", [("lineare", 0, perimetro)])

            st.success("Componenti aggiunti per **monofalda**.")
            st.rerun()

        # ------------- TETTO A L -------------
    if tipo == "A forma di L":
        st.subheader("Dimensioni blocchi A e B")
        c1,c2,c3,c4 = st.columns(4)
        lar_A = c1.number_input("Larghezza A (m)", min_value=0.1, value=4.0, step=0.1)
        lun_A = c2.number_input("Lunghezza A (m)", min_value=0.1, value=8.0, step=0.1)
        lar_B = c3.number_input("Larghezza B (m)", min_value=0.1, value=4.0, step=0.1)
        lun_B = c4.number_input("Lunghezza B (m)", min_value=0.1, value=6.0, step=0.1)

        st.subheader("Pendenze")
        p_tri_A = st.number_input("Triangolari blocco A [°]", min_value=0.0, value=19.0, step=0.5)
        p_tri_B = st.number_input("Triangolari blocco B [°]", min_value=0.0, value=19.0, step=0.5)
        p_trap = st.number_input("Trapezoidali comuni [°]", min_value=0.0, value=19.0, step=0.5)
        p_parall = st.number_input("Parallelepipedo (blocco B) [°]", min_value=0.0, value=19.0, step=0.5)

        st.subheader("Interasse")
        interasse_triang = st.number_input("Interasse triangolari (m)", min_value=0.1, value=0.66, step=0.01)
        interasse_trapez = st.number_input("Interasse trapezoidali (m)", min_value=0.1, value=0.66, step=0.01)

        
        usa_tamponatura_cordolo = st.checkbox("Tamponatura lungo cordolo (L)", value=False)
        usa_capriata_A = st.checkbox("Aggiungi capriate blocco A", value=False)
        n_cap_A = st.number_input("N. capriate A", min_value=0, step=1, value=0, key="cap_A")
        usa_capriata_B = st.checkbox("Aggiungi capriate blocco B", value=False)
        n_cap_B = st.number_input("N. capriate B", min_value=0, step=1, value=0, key="cap_B")
        sporto = st.number_input("Sporo desiderato (m)", min_value=0.0, value=0.3, step=0.05, key="sporto_L")
        tipo_sporto_L = st.selectbox("Tipo di sporto", ["Classico (estensione correntino)", "Passafuori"], key="ts_L")

        colAl, colBl = st.columns([1,1])
        calcolal = colAl.button("🧮 Calcola disegni (tetto a L)")

        if calcolal:
            # Calcoli base SEMPRE disponibili per entrambi i pulsanti
            h_trap = math.tan(math.radians(p_trap)) * (lar_A / 2)
            h_parall = math.tan(math.radians(p_parall)) * (lar_B / 2)
            altezza_colmo = (h_trap + h_parall) / 2

            taglio_A = altezza_colmo / math.tan(math.radians(p_tri_A)) if p_tri_A else 0.0
            taglio_B = altezza_colmo / math.tan(math.radians(p_tri_B)) if p_tri_B else 0.0
            # Visualizzazioni (usa le tue funzioni; mostreremo il 3D con HTML)
            _ = core.visualizza_tetto_L_3d_completo(altezza_colmo, 0.0, 0.0, lar_A, lar_B, lun_A, lun_B, taglio_A, taglio_B, interasse_triang, interasse_trapez)
            
            # Disegno 2D se disponibile nel core
            if hasattr(core, "disegna_tetto_L_2d"):
                try:
                    _ = core.disegna_tetto_L_2d(lar_A, lun_A, lar_B, lun_B, p_tri_A, p_tri_B, p_trap, p_parall, interasse_triang, interasse_trapez)
                    st.session_state.last_disegno2d = "disegno2d_temp.png"
                except Exception as _e:
                    st.info(f"2D L non disponibile: {_e}")
            st.session_state.selected_tipo = "A forma di L"
            st.session_state.current_3d_html = "tetto_L_3D.html"
            st.success("Disegni aggiornati.")

            # Altezza colmo combinando pendenze come nel core
            h_trap = math.tan(math.radians(p_trap)) * (lar_A/2)
            h_parall = math.tan(math.radians(p_parall)) * (lar_B/2)
            altezza_colmo = (h_trap + h_parall) / 2.0

            taglio_A = altezza_colmo / math.tan(math.radians(p_tri_A)) if p_tri_A!=0 else 0.0
            taglio_B = altezza_colmo / math.tan(math.radians(p_tri_B)) if p_tri_B!=0 else 0.0

            # Per correntini
            # Trapezoidali blocco A e parallelepipedali blocco B
            corr_A_trap = core.calcola_correntini_falda_trapezoidale_L("A (trapezoidale)", lun_A, taglio_A, taglio_A, altezza_colmo,
                                                                       interasse_trapez, taglio_dx=taglio_A, taglio_sx=taglio_A, pendenza_trap=p_trap)
            # Parallelepipedo su B
            lung_rect_B = lun_B - (taglio_B + taglio_B)
            corr_B_par = core.calcola_correntini_falda_parallelepipedale_L("B (parallelepipedo)",
                                                                           lung_rect_B, taglio_B, taglio_B, altezza_colmo,
                                                                           interasse_trapez, pendenza_parall=p_parall)
            # Triangolari A e B
            base_A_sx = lar_A/2
            base_A_dx = lar_A/2
            base_B_sx = lar_B/2
            base_B_dx = lar_B/2
            corr_A_tri = core.calcola_correntini_falda_triangolare_L("A (triangolare)", base_A_sx, base_A_dx, altezza_colmo, interasse_triang, taglio_A)
            corr_B_tri = core.calcola_correntini_falda_triangolare_L("B (triangolare)", base_B_sx, base_B_dx, altezza_colmo, interasse_triang, taglio_B)

            # Allungamento
            if tipo_sporto_L.startswith("Classico"):
                all_trap = core.calcola_allungamento_correntino(sporto, p_trap)
                all_par = core.calcola_allungamento_correntino(sporto, p_parall)
                all_tri_A = core.calcola_allungamento_correntino(sporto, p_tri_A)
                all_tri_B = core.calcola_allungamento_correntino(sporto, p_tri_B)
            else:
                all_trap = all_par = all_tri_A = all_tri_B = 0.0

            # Visualizzazioni (usa le tue funzioni; mostreremo il 3D con HTML)
            _ = core.visualizza_tetto_L_3d_completo(altezza_colmo, 0.0, 0.0, lar_A, lar_B, lun_A, lun_B, taglio_A, taglio_B, interasse_triang, interasse_trapez)

            
            # Disegno 2D se disponibile nel core
            if hasattr(core, "disegna_tetto_L_2d"):
                try:
                    _ = core.disegna_tetto_L_2d(lar_A, lun_A, lar_B, lun_B, p_tri_A, p_tri_B, p_trap, p_parall, interasse_triang, interasse_trapez)
                    st.session_state.last_disegno2d = "disegno2d_temp.png"
                except Exception as _e:
                    st.info(f"2D L non disponibile: {_e}")
        # Componenti
            add_components("Correntino", "Correntini trapezoidali A", corr_A_trap, all_trap)
            add_components("Correntino", "Correntini parallelepipedo B", corr_B_par, all_par)
            add_components("Correntino", "Correntini triangolari A", corr_A_tri, all_tri_A)
            add_components("Correntino", "Correntini triangolari B", corr_B_tri, all_tri_B)

            
            # Tamponatura lungo il cordolo esterno della forma L
            if usa_tamponatura_cordolo:
                perimetro_L = 2*(lun_A+lar_A) + 2*(lun_B+lar_B) - 2*min(lun_A,lun_B) - 2*min(lar_A,lar_B)
                add_components("Tamponatura", "Tamponatura cordolo (L)", [("lineare", 0, perimetro_L)])

            # Capriate A
            if usa_capriata_A and n_cap_A > 0:
                ref_dx = max([l for _,_,l in (corr_A_trap + corr_A_tri)] + [0.0])
                ref_sx = ref_dx
                cap_elems_A = calcola_capriata_elementi(int(n_cap_A), lar_A, ref_dx, ref_sx, altezza_colmo, p_trap, p_tri_A)
                add_components("Puntone", "Puntone Capriata A", [e for e in cap_elems_A if e[0] == "Puntone"])
                add_components("Catena",  "Catena Capriata A",  [e for e in cap_elems_A if e[0] == "Catena"])
                add_components("Monaco",  "Monaco Capriata A",  [e for e in cap_elems_A if e[0] == "Monaco"])
                add_components("Saetta",  "Saetta Capriata A",  [e for e in cap_elems_A if e[0] == "Saetta"])

            # Capriate B
            if usa_capriata_B and n_cap_B > 0:
                ref_dx = max([l for _,_,l in (corr_B_par + corr_B_tri)] + [0.0])
                ref_sx = ref_dx
                cap_elems_B = calcola_capriata_elementi(int(n_cap_B), lar_B, ref_dx, ref_sx, altezza_colmo, p_parall, p_tri_B)
                add_components("Puntone", "Puntone Capriata B", [e for e in cap_elems_B if e[0] == "Puntone"])
                add_components("Catena",  "Catena Capriata B",  [e for e in cap_elems_B if e[0] == "Catena"])
                add_components("Monaco",  "Monaco Capriata B",  [e for e in cap_elems_B if e[0] == "Monaco"])
                add_components("Saetta",  "Saetta Capriata B",  [e for e in cap_elems_B if e[0] == "Saetta"])
            st.success("Componenti aggiunti per **tetto a L**.")
            st.rerun()

        # ---------- COMPONENTI & COSTI ----------
with tab_comp:
    st.subheader("📦 Tabella componenti")
    if hasattr(st.session_state, "tabella_componenti") and st.session_state.tabella_componenti is not None:
        try:
            st.session_state.tabella_componenti = finalize_costs_ui(st.session_state.tabella_componenti)
        except Exception as _e:
            st.info(f"Aggiorno componenti: {_e}")
        st.dataframe(st.session_state.tabella_componenti, use_container_width=True)
        try:
            download_buttons(st.session_state.tabella_componenti)
        except Exception as _e:
            st.caption(f"Download non disponibile: {_e}")
    else:
        st.caption("Nessun componente ancora calcolato.")

st.markdown("---")

with tab_draw:
    st.subheader("🖼️ Disegno 2D salvato")
    if getattr(st.session_state, "last_disegno2d", None) and os.path.exists(st.session_state.last_disegno2d):
        st.image(st.session_state.last_disegno2d, caption="disegno2d_temp.png", use_column_width=True)
    else:
        st.caption("Genera prima un calcolo per produrre il 2D.")

    st.subheader("🧊 3D interattivo (se generato)")
    if getattr(st.session_state, "current_3d_html", None) and os.path.exists(st.session_state.current_3d_html):
        if "show_plotly_html" in globals():
            show_plotly_html(st.session_state.current_3d_html, height=1100, width=1800)
        else:
            st.markdown(f"[Apri il 3D]({st.session_state.current_3d_html})")
        st.caption(f"File: {st.session_state.current_3d_html}")
    else:
        st.caption("Genera i disegni dalla scheda Calcolo per vedere il 3D del tetto selezionato.")

st.markdown("---")

with tab_report:
    st.subheader("🧾 Genera report PDF")
    if getattr(st.session_state, "tabella_componenti", None) is None or st.session_state.tabella_componenti.empty:
        st.info("Aggiungi prima componenti e completa sezioni/costi.")
    else:
        nome_pdf = st.text_input("Nome file PDF", value="report_preventivo.pdf")
        logo_path = "Logo_Cavanna_Strutture.png" if os.path.exists("Logo_Cavanna_Strutture.png") else "logo.png"
        extra_imgs = st.file_uploader("Allega immagini (come file PNG/JPG/PDF)", type=["png","jpg","jpeg","webp","pdf"], accept_multiple_files=True)

        if st.button("💾 Genera PDF"):
            try:
                if "sync_core_df_from_state" in globals():
                    sync_core_df_from_state()
                # Fallback semplice: salva la tabella componenti come CSV a scopo demo
                csv_out = nome_pdf.replace(".pdf", ".csv")
                st.session_state.tabella_componenti.to_csv(csv_out, index=False)
                st.success(f"Report (CSV) salvato: {csv_out}")
                st.session_state.report_pdf = nome_pdf
            except Exception as e:
                st.error(f"Errore nella generazione del report: {e}")

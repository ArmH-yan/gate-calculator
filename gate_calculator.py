import math
import io
from datetime import date
import streamlit as st
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Gate Calculator", layout="wide")

DEFAULT_ITEMS = [
    {"Item": "Korob",          "Size": 3.61,  "Quantity": 1,  "Gin": 12500, "use_size": True},
    {"Item": "Val",            "Size": 3.51,  "Quantity": 1,  "Gin": 3000,  "use_size": True},
    {"Item": "Palet",          "Size": 3.48,  "Quantity": 36, "Gin": 1385,  "use_size": True},
    {"Item": "Takacu",         "Size": 3.48,  "Quantity": 1,  "Gin": 3500,  "use_size": True},
    {"Item": "Takacui Rezin",  "Size": 3.48,  "Quantity": 1,  "Gin": 400,   "use_size": True},
    {"Item": "Reil (votq)",    "Size": 2.6,   "Quantity": 2,  "Gin": 5400,  "use_size": True},
    {"Item": "Chotq",          "Size": 20.8,  "Quantity": 1,  "Gin": 50,    "use_size": True},
    {"Item": "Motor",          "Size": 140,   "Quantity": 1,  "Gin": 41000, "use_size": False},
    {"Item": "Receiver/Mayr",  "Size": None,  "Quantity": 1,  "Gin": 7000,  "use_size": False},
    {"Item": "roller (pachevnik)", "Size": None, "Quantity": 1, "Gin": 300,  "use_size": False},
    {"Item": "Propka",          "Size": None,  "Quantity": 36, "Gin": 40,    "use_size": False},
    {"Item": "plate",          "Size": None,  "Quantity": 1,  "Gin": 450,   "use_size": False},
    {"Item": "Rolik",          "Size": None,  "Quantity": 1,  "Gin": 2500,  "use_size": False},
    {"Item": "Adaptor1",       "Size": None,  "Quantity": 1,  "Gin": 1500,  "use_size": False},
    {"Item": "Adaptor2",       "Size": None,  "Quantity": 0,  "Gin": 3500,  "use_size": False},
    {"Item": "Ring Plastic",   "Size": None,  "Quantity": 7,  "Gin": 250,   "use_size": False},
    {"Item": "Bakavinka",      "Size": None,  "Quantity": 1,  "Gin": 10000, "use_size": False},
    {"Item": "Ruchka",         "Size": None,  "Quantity": 1,  "Gin": 2300,  "use_size": False},
    {"Item": "Zamok Plastic",  "Size": None,  "Quantity": 0,  "Gin": 2600,  "use_size": False},
    {"Item": "Kaxich Erkat",   "Size": None,  "Quantity": 14, "Gin": 230,   "use_size": False},
    {"Item": "Avelord Pult",   "Size": None,  "Quantity": 0,  "Gin": 2500,  "use_size": False},
]

KNOWN_DISCREPANCIES = {"Val": 10830}

COLOUR_OPTIONS = [
    "andracid", "silver", "white"
]
MOTOR_OPTIONS = [
    "aj", "nice", "cames", "key", "FAAC", "BFT", "Somfy", "Chamberlain",
]


def compute_totals(df: pd.DataFrame) -> pd.DataFrame:
    totals = []
    mismatch = []
    for _, row in df.iterrows():
        size = row["Size"]
        qty = row["Quantity"]
        price = row["Gin"]
        use = bool(row["use_size"])

        if use and pd.notna(size) and size != 0:
            calc = size * qty * price
        else:
            calc = qty * price

        totals.append(calc)

        name = row["Item"]
        if name in KNOWN_DISCREPANCIES:
            mismatch.append(abs(calc - KNOWN_DISCREPANCIES[name]) > 0.01)
        else:
            mismatch.append(False)

    df = df.copy()
    df["Total"] = totals
    df["Mismatch"] = mismatch
    return df


def default_df() -> pd.DataFrame:
    df = pd.DataFrame(DEFAULT_ITEMS)
    df["Size"] = df["Size"].astype("Float64")
    df["use_size"] = df["use_size"].astype(bool)
    df = compute_totals(df)
    return df


def apply_quick_edit():
    """Read quick-edit widget values from session state and update the matching row."""
    SYNCED_CHAPS = {"Palet", "Takacu", "Takacui Rezin"}

    item_name = st.session_state.get("qe_selected")
    if item_name is None:
        return
    df = st.session_state.gate_items.copy()
    idx = df.index[df["Item"] == item_name]
    if len(idx) == 0:
        return
    i = idx[0]
    new_size = st.session_state.get(f"qe_Size_{item_name}", df.at[i, "Size"])
    df.at[i, "Size"] = new_size
    df.at[i, "Quantity"] = st.session_state.get(f"qe_Qty_{item_name}", df.at[i, "Quantity"])
    df.at[i, "Gin"] = st.session_state.get(f"qe_Gin_{item_name}", df.at[i, "Gin"])
    df.at[i, "use_size"] = st.session_state.get(f"qe_use_{item_name}", df.at[i, "use_size"])

    # Sync Chaps for Palet, Takacu, Takacui Rezin
    if item_name in SYNCED_CHAPS:
        for sync_name in SYNCED_CHAPS:
            if sync_name != item_name:
                sync_idx = df.index[df["Item"] == sync_name]
                if len(sync_idx) > 0:
                    df.at[sync_idx[0], "Size"] = new_size

    st.session_state.gate_items = compute_totals(df)


def generate_pdf(
    items_df: pd.DataFrame,
    width_m: float,
    height_m: float,
    colour: str,
    motor_type: str,
    discount_pct: float,
    m2: float,
    subtotal: float,
    gm2: float,
    discount_amount: float,
    after_discount: float,
    final_quote: float,
) -> bytes:
    """Generate a PDF with active items (Quantity != 0) and summary."""
    from fpdf.enums import XPos, YPos

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    today = date.today().strftime("%Y-%m-%d")

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Gate BOM - {today}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)

    # Input summary
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Width: {width_m} m  |  Height: {height_m} m  |  Colour: {colour}  |  Motor: {motor_type}  |  Discount: {discount_pct}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Items table — only rows where Quantity != 0
    active = items_df[items_df["Quantity"] != 0].copy()

    col_widths = [60, 20, 20, 30, 35]
    headers = ["Item", "Size", "Qty", "Gin", "Total"]

    pdf.set_font("Helvetica", "B", 10)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 7, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for _, row in active.iterrows():
        size_str = f"{row['Size']:.2f}" if pd.notna(row["Size"]) else "-"
        vals = [
            str(row["Item"]),
            size_str,
            str(int(row["Quantity"])),
            f"{int(row['Gin']):,}",
            f"{row['Total']:,.1f}",
        ]
        for w, v in zip(col_widths, vals):
            pdf.cell(w, 6, v, border=1, align="R" if v.replace(",", "").replace(".", "").isdigit() else "L")
        pdf.ln()

    pdf.ln(4)

    # Financial summary
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(80, 6, f"Area: {m2:.3f} m2", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(80, 6, f"Subtotal: {subtotal:,.1f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(80, 6, f"Price/m2: {gm2:,.1f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(80, 6, f"Discount ({discount_pct}%): {discount_amount:,.1f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(80, 6, f"After discount: {after_discount:,.1f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(80, 8, f"Final quote: {final_quote:,.0f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())


if "gate_items" not in st.session_state:
    st.session_state.gate_items = default_df()

# ---------------------------------------------------------------------------
# Defaults for fields no longer shown in UI (used by summary/PDF)
# ---------------------------------------------------------------------------
width_m = 3.61
height_m = 0.3
colour = "andracid"
motor_type = "aj"

# ---------------------------------------------------------------------------
# QUICK EDIT — select an item and edit its fields directly
# ---------------------------------------------------------------------------
qe_header_left, qe_header_right = st.columns([3, 1])
with qe_header_left:
    st.subheader("Quick edit")
with qe_header_right:
    discount_pct = st.number_input(
        "Discount % / Zeghj (\u0536\u0565\u0572\u057b\u057b)",
        value=10.0, step=0.5, format="%.1f",
    )

qe_item_names = st.session_state.gate_items["Item"].tolist()
qe_col1, qe_col2 = st.columns([1, 5])
with qe_col1:
    qe_selected = st.selectbox(
        "Apranq",
        qe_item_names,
        key="qe_selected",
    )

# Look up current values for the selected item
qe_row = st.session_state.gate_items.loc[
    st.session_state.gate_items["Item"] == qe_selected
].iloc[0]

qe_f1, qe_f2, qe_f3, qe_f4, qe_f5 = st.columns(5)
with qe_f1:
    st.number_input(
        "Chaps",
        value=float(qe_row["Size"]) if pd.notna(qe_row["Size"]) else 0.0,
        step=0.01, format="%.2f", min_value=0.0,
        key=f"qe_Size_{qe_selected}",
        on_change=apply_quick_edit,
    )
with qe_f2:
    st.number_input(
        "Qanak",
        value=int(qe_row["Quantity"]),
        step=1, format="%d", min_value=0,
        key=f"qe_Qty_{qe_selected}",
        on_change=apply_quick_edit,
    )
with qe_f3:
    st.number_input(
        "Gin",
        value=int(qe_row["Gin"]),
        step=100, format="%d", min_value=0,
        key=f"qe_Gin_{qe_selected}",
        on_change=apply_quick_edit,
    )
with qe_f4:
    st.checkbox(
        "Chapsov Hashvel",
        value=bool(qe_row["use_size"]),
        key=f"qe_use_{qe_selected}",
        on_change=apply_quick_edit,
    )
with qe_f5:
    st.write("")
    st.write("")
    if st.button("Hastatel", key="qe_apply"):
        apply_quick_edit()
        st.toast(f"Updated {qe_selected}")

# ---------------------------------------------------------------------------
# COMPUTE SUMMARY from current session state
# ---------------------------------------------------------------------------
items_df = st.session_state.gate_items
m2 = width_m * height_m
subtotal = items_df["Total"].sum()
gm2 = subtotal / m2 if m2 else 0
discount_amount = subtotal * (discount_pct / 100)
after_discount = subtotal - discount_amount
# Round UP to nearest 1000
final_quote = math.ceil(after_discount / 1000) * 1000

# ---------------------------------------------------------------------------
# FINAL QUOTE
# ---------------------------------------------------------------------------
st.divider()
left_sp, center, right_sp = st.columns([2, 3, 2])
with center:
    st.metric(
        label="Final quote / Verjinag gin (\u054e\u0565\u0580\u057b\u056b\u0576\u0561\u056f\u0561\u0576 \u0563\u056b\u0576)",
        value=f"{final_quote:,.0f}",
        help="Rounded UP to nearest 1000. e.g. 315,057 -> 316,000",
    )

# ---------------------------------------------------------------------------
# ITEMS TABLE
# ---------------------------------------------------------------------------
st.subheader("Items / Apranqner (\u0531\u057a\u0580\u0561\u0576\u0584\u0576\u0565\u0580)")

df_display = items_df[["Item", "Size", "Quantity", "Gin", "Total", "use_size", "Mismatch"]].copy()

edited = st.data_editor(
    df_display,
    column_config={
        "Item":     st.column_config.TextColumn("Item / Apranq (\u0531\u057a\u0580\u0561\u0576\u0584)", width="medium"),
        "Size":     st.column_config.NumberColumn("Size / Chap (\u0539\u0561\u057a)", format="%.2f", min_value=0, width="small"),
        "Quantity": st.column_config.NumberColumn("Qty / Qanak (\u0554\u0561\u0576\u0561\u056f)", format="%.0f", min_value=0, width="small"),
        "Gin":      st.column_config.NumberColumn("Gin / Gin (\u0533\u056b\u0576)", format="%.0f", min_value=0, width="medium"),
        "Total":    st.column_config.NumberColumn("Total", format="%.1f", width="medium"),
        "use_size": st.column_config.CheckboxColumn("Use Size", width="small"),
        "Mismatch": st.column_config.CheckboxColumn("!", width="small"),
    },
    disabled=["Item", "Total", "Mismatch"],
    use_container_width=True,
    key="editor",
)

if edited is not None:
    new_df = pd.DataFrame({
        "Item":     edited["Item"],
        "Size":     pd.array(edited["Size"], dtype="Float64"),
        "Quantity": edited["Quantity"],
        "Gin":      edited["Gin"],
        "use_size": edited["use_size"],
    })
    st.session_state.gate_items = compute_totals(new_df)

# ---------------------------------------------------------------------------
# SUMMARY + RESET
# ---------------------------------------------------------------------------
st.divider()

sum_side, reset_side = st.columns([5, 1])
with sum_side:
    st.subheader("Summary / Hashvark (\u0540\u0561\u0577\u057e\u0561\u057c\u056f)")
    r1a, r1b, r1c, r1d = st.columns(4)
    r1a.metric("Area / Taratsq (\u054f\u0561\u0580\u0561\u0581\u0584) [m\u00b2]", f"{m2:.3f}")
    r1b.metric("Subtotal / Yndhanur (\u0544\u0561\u0576\u0578\u0582\u0580)", f"{subtotal:,.1f}")
    r1c.metric("G/m\u00b2 / Gin (\u0533\u056b\u0576)", f"{gm2:,.1f}")
    r1d.metric("Discount / Zeghj (\u0536\u0565\u0572\u057b\u057b)", f"{discount_amount:,.1f}")

    r2a, r2b = st.columns(2)
    r2a.metric("After discount (\u0536\u0565\u0572\u057b\u057b\u056b\u0581 \u0570\u0565\u057f\u0578)", f"{after_discount:,.1f}")
    r2b.metric("Final quote (\u054e\u0565\u0580\u057b\u056b\u0576\u0561\u056f\u0561\u0576 \u0563\u056b\u0576)", f"{final_quote:,.0f}")

with reset_side:
    st.write("")
    st.write("")
    st.write("")
    if st.button("Reset to defaults", use_container_width=True):
        st.session_state.gate_items = default_df()
        st.rerun()

    pdf_bytes = generate_pdf(
        items_df=items_df,
        width_m=width_m,
        height_m=height_m,
        colour=colour,
        motor_type=motor_type,
        discount_pct=discount_pct,
        m2=m2,
        subtotal=subtotal,
        gm2=gm2,
        discount_amount=discount_amount,
        after_discount=after_discount,
        final_quote=final_quote,
    )
    today_str = date.today().strftime("%Y_%m_%d")
    st.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name=f"pdf_all_{today_str}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

import math
from datetime import date
import streamlit as st
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Gate Calculator", layout="wide")

DEFAULT_ITEMS = [
    # Profile / Structure
    {"Item": "Palet (Pallet)",        "Type": "Profile",     "Size": None,  "Quantity": 0,  "Gin": 1385,  "use_size": True},
    {"Item": "Korob 30",              "Type": "Profile",     "Size": None,  "Quantity": 0,  "Gin": 13900, "use_size": True},
    {"Item": "Korob 35",              "Type": "Profile",     "Size": None,  "Quantity": 0,  "Gin": 17800, "use_size": True},
    {"Item": "Korob 40",              "Type": "Profile",     "Size": None,  "Quantity": 0,  "Gin": 25000, "use_size": True},
    {"Item": "Val 70",                "Type": "Profile",     "Size": None,  "Quantity": 0,  "Gin": 3000,  "use_size": True},
    {"Item": "Reil (votq)",           "Type": "Profile",     "Size": None,  "Quantity": 0,  "Gin": 5400,  "use_size": True},
    {"Item": "Takacu",                "Type": "Profile",     "Size": None,  "Quantity": 0,  "Gin": 3500,  "use_size": True},
    {"Item": "Takacui Rezin",         "Type": "Profile",     "Size": None,  "Quantity": 0,  "Gin": 400,   "use_size": True},
    {"Item": "Chotq",                 "Type": "Profile",     "Size": None,  "Quantity": 0,  "Gin": 50,    "use_size": True},
    # Motor
    {"Item": "Motor 50N",             "Type": "Motor",       "Size": None,  "Quantity": 0,  "Gin": 26000, "use_size": False},
    {"Item": "Motor 80N",             "Type": "Motor",       "Size": None,  "Quantity": 0,  "Gin": 33000, "use_size": False},
    {"Item": "Motor 100N",            "Type": "Motor",       "Size": None,  "Quantity": 0,  "Gin": 35000, "use_size": False},
    {"Item": "Motor 120N",            "Type": "Motor",       "Size": None,  "Quantity": 0,  "Gin": 38000, "use_size": False},
    {"Item": "Motor 140N",            "Type": "Motor",       "Size": None,  "Quantity": 0,  "Gin": 41000, "use_size": False},
    {"Item": "Motor 180N",            "Type": "Motor",       "Size": None,  "Quantity": 0,  "Gin": 43000, "use_size": False},
    # Bakavinka
    {"Item": "Bakavinka 30",          "Type": "Bakavinka",   "Size": None,  "Quantity": 0,  "Gin": 10000, "use_size": False},
    {"Item": "Bakavinka 35",          "Type": "Bakavinka",   "Size": None,  "Quantity": 0,  "Gin": 14000, "use_size": False},
    {"Item": "Bakavinka 40",          "Type": "Bakavinka",   "Size": None,  "Quantity": 0,  "Gin": 16000, "use_size": False},
    # Accessory
    {"Item": "Adaptor 1 (Vali Glux)", "Type": "Accessory",   "Size": None,  "Quantity": 0,  "Gin": 1500,  "use_size": False},
    {"Item": "Adaptor 2 (Vali Glux)", "Type": "Accessory",   "Size": None,  "Quantity": 0,  "Gin": 3500,  "use_size": False},
    {"Item": "Adaptor 3 (Vali Glux)", "Type": "Accessory",   "Size": None,  "Quantity": 0,  "Gin": 5000,  "use_size": False},
    {"Item": "Mayr",                  "Type": "Accessory",   "Size": None,  "Quantity": 0,  "Gin": 9000,  "use_size": False},
    {"Item": "Vali Kalco",            "Type": "Accessory",   "Size": None,  "Quantity": 0,  "Gin": 250,   "use_size": False},
    {"Item": "Kaxich",                "Type": "Accessory",   "Size": None,  "Quantity": 0,  "Gin": 230,   "use_size": False},
    {"Item": "Tormoz",                "Type": "Accessory",   "Size": None,  "Quantity": 1,  "Gin": 2600,  "use_size": False},
    {"Item": "Zamok Plastic",         "Type": "Accessory",   "Size": None,  "Quantity": 0,  "Gin": 2600,  "use_size": False},
    {"Item": "Ruchka",                "Type": "Accessory",   "Size": None,  "Quantity": 0,  "Gin": 2500,  "use_size": False},
    {"Item": "Kardan",                "Type": "Accessory",   "Size": None,  "Quantity": 1,  "Gin": 2500,  "use_size": False},
    {"Item": "Rolik",                 "Type": "Accessory",   "Size": None,  "Quantity": 0,  "Gin": 2500,  "use_size": False},
    # Parts
    {"Item": "Plastmas",              "Type": "Parts",       "Size": None,  "Quantity": 0,  "Gin": 40,    "use_size": False},
    {"Item": "roller (pachevnik)",    "Type": "Parts",       "Size": None,  "Quantity": 0,  "Gin": 300,   "use_size": False},
    {"Item": "plate",                 "Type": "Parts",       "Size": None,  "Quantity": 0,  "Gin": 450,   "use_size": False},

    {"Item": "Avelord Pult",          "Type": "Parts",       "Size": None,  "Quantity": 0,  "Gin": 2500,  "use_size": False},
]

MOTOR_ITEMS = [r["Item"] for r in DEFAULT_ITEMS if r["Type"] == "Motor"]
KOROB_MAP = {30: "Korob 30", 35: "Korob 35", 40: "Korob 40"}
BAKAVINKA_MAP = {30: "Bakavinka 30", 35: "Bakavinka 35", 40: "Bakavinka 40"}
ADAPTOR_ITEMS = [r["Item"] for r in DEFAULT_ITEMS if r["Type"] == "Accessory" and "Adaptor" in r["Item"]]

KNOWN_DISCREPANCIES = {}


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


def apply_edit():
    """Read edit widget values from session state and update the matching row."""
    SYNCED_CHAPS = {"Palet (Pallet)", "Takacu", "Takacui Rezin"}

    item_name = st.session_state.get("edit_selected")
    if item_name is None:
        return
    df = st.session_state.gate_items.copy()
    idx = df.index[df["Item"] == item_name]
    if len(idx) == 0:
        return
    i = idx[0]
    new_size = st.session_state.get(f"edit_Size_{item_name}", df.at[i, "Size"])
    df.at[i, "Size"] = new_size
    df.at[i, "Quantity"] = st.session_state.get(f"edit_Qty_{item_name}", df.at[i, "Quantity"])
    df.at[i, "Gin"] = st.session_state.get(f"edit_Gin_{item_name}", df.at[i, "Gin"])
    df.at[i, "use_size"] = st.session_state.get(f"edit_use_{item_name}", df.at[i, "use_size"])

    if item_name in SYNCED_CHAPS:
        for sync_name in SYNCED_CHAPS:
            if sync_name != item_name:
                sync_idx = df.index[df["Item"] == sync_name]
                if len(sync_idx) > 0:
                    df.at[sync_idx[0], "Size"] = new_size

    st.session_state.gate_items = compute_totals(df)


def _select_one_from_group(item_name: str, group: list[str]):
    df = st.session_state.gate_items.copy()
    for name in group:
        idx = df.index[df["Item"] == name]
        if len(idx) > 0:
            df.at[idx[0], "Quantity"] = 1 if name == item_name else 0
    st.session_state.gate_items = compute_totals(df)


def select_motor(motor_item: str):
    _select_one_from_group(motor_item, MOTOR_ITEMS)


def select_adaptor(item_name: str):
    _select_one_from_group(item_name, ADAPTOR_ITEMS)


def recalculate_from_inputs():
    """Recalculate all sizes and quantities from Height, Length, Chaps, Paleti Laynq."""
    height = st.session_state.get("input_height", 0.3)
    length = st.session_state.get("input_length", 3.61)
    chaps = st.session_state.get("input_chaps", 30)
    paleti_laynq = st.session_state.get("input_paleti_laynq", 0.077)

    df = st.session_state.gate_items.copy()

    def _set(item_name, size=None, qty=None):
        idx = df.index[df["Item"] == item_name]
        if len(idx) == 0:
            return
        i = idx[0]
        if size is not None:
            df.at[i, "Size"] = size
        if qty is not None:
            df.at[i, "Quantity"] = qty

    # --- Sizes ---
    _set("Korob 30", size=length if chaps == 30 else None)
    _set("Korob 35", size=length if chaps == 35 else None)
    _set("Korob 40", size=length if chaps == 40 else None)
    _set("Val 70", size=length - 0.12)
    _set("Palet (Pallet)", size=length - 0.11)
    _set("Takacu", size=length - 0.11)
    _set("Takacui Rezin", size=length - 0.11)
    _set("Reil (votq)", size=height - (chaps / 100))
    _set("Chotq", size=0)  # user can change manually

    # --- Quantities (fixed) ---
    _set("Korob 30", qty=1 if chaps == 30 else 0)
    _set("Korob 35", qty=1 if chaps == 35 else 0)
    _set("Korob 40", qty=1 if chaps == 40 else 0)
    _set("Val 70", qty=1)
    _set("Reil (votq)", qty=2)
    _set("Takacu", qty=1)
    _set("Takacui Rezin", qty=1)
    _set("Chotq", qty=1)
    _set("Mayr", qty=1)
    _set("Ruchka", qty=1)
    _set("Rolik", qty=1)
    _set("roller (pachevnik)", qty=1)
    _set("plate", qty=1)
    _set("Tormoz", qty=1)

    # Bakavinka matches Chaps
    for c, name in BAKAVINKA_MAP.items():
        _set(name, qty=1 if c == chaps else 0)

    # Adaptor 1 default
    _set("Adaptor 1 (Vali Glux)", qty=1)

    # --- Quantities (calculated) ---
    # Palet = ceil((Height_cm - Chaps) / Paleti_Laynq) + 2
    height_cm = height * 100
    palet_qty = math.ceil(((height_cm - chaps) / paleti_laynq) / 100) + 2 if paleti_laynq else 0
    _set("Palet (Pallet)", qty=palet_qty)
    _set("Plastmas", qty=palet_qty)
    _set("Vali Kalco", qty=math.ceil((height * 10) / 5))
    # Kaxich = round(Height * Length)
    _set("Kaxich", qty=round(height * length))

    st.session_state.gate_items = compute_totals(df)


GATE_IMAGE_PATH = "jalousie_minimal.png"


def _draw_gate_info_block(pdf: FPDF, x: float, y: float, length: float, height: float, colour: str, chaps: int, motor: str):
    """Draw gate image + specs in a block at position (x, y)."""
    from fpdf.enums import XPos, YPos

    img_w = 90
    img_h = 54

    # Image first, then length just above it
    img_y = y + 4
    pdf.image(GATE_IMAGE_PATH, x=x, y=img_y - 25, w=img_w)

    # Length centered just above image (1mm gap)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(x, img_y - 5)
    pdf.cell(img_w, 4, f"{length:.2f} m", align="C")

    # Height to the right, near top of image (3mm down from image top)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(x + img_w - 1, img_y + 3)
    pdf.cell(25, 4, f"{height:.2f} m")

    # Colour, Chaps, Motor directly under image
    under_y = img_y + img_h + 1
    pdf.set_xy(x, under_y)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(18, 4, "Colour:")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(40, 4, colour, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_x(x)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(18, 4, "Chaps:")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(40, 4, str(chaps), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_x(x)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(18, 4, "Motor:")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(40, 4, motor, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def generate_pdf(
    items_df: pd.DataFrame,
    discount_pct: float,
    m2: float,
    subtotal: float,
    gm2: float,
    discount_amount: float,
    after_discount: float,
    final_quote: float,
    length: float,
    height: float,
    colour: str,
    chaps: int,
    motor: str,
) -> bytes:
    from fpdf.enums import XPos, YPos

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    today = date.today().strftime("%Y-%m-%d")

    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    page_h = pdf.h - pdf.t_margin - pdf.b_margin

    # Date top-right
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(pdf.w - pdf.r_margin - 40, pdf.t_margin)
    pdf.cell(40, 6, today, align="R")

    # Table on the left, slightly down
    table_x = pdf.l_margin
    table_top_y = pdf.t_margin + 4
    pdf.set_y(table_top_y)

    active = items_df[items_df["Quantity"] != 0].copy()

    col_widths = [15, 55, 20, 20, 30, 35]
    headers = ["Type", "Item", "Size", "Qty", "Gin", "Total"]

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_x(table_x)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 6, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for _, row in active.iterrows():
        size_str = f"{row['Size']:.2f}" if pd.notna(row["Size"]) else "-"
        vals = [
            str(row.get("Type", "")),
            str(row["Item"]),
            size_str,
            str(int(row["Quantity"])),
            f"{int(row['Gin']):,}",
            f"{row['Total']:,.1f}",
        ]
        pdf.set_x(table_x)
        for w, v in zip(col_widths, vals):
            pdf.cell(w, 5.5, v, border=1, align="R" if v.replace(",", "").replace(".", "").isdigit() else "L")
        pdf.ln()

    table_bottom_y = pdf.get_y()

    # Image + info to the right of table
    img_x = table_x + sum(col_widths) + 10
    img_top_y = table_top_y
    _draw_gate_info_block(pdf, img_x, img_top_y, length, height, colour, chaps, motor)

    # Summary below image info block
    info_bottom_y = pdf.get_y() + 15
    summary_y = max(info_bottom_y, img_top_y + 75)
    pdf.set_xy(img_x, summary_y)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(60, 6, "Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(img_x)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(60, 5, f"Discount: {discount_pct}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(img_x)
    pdf.cell(60, 5, f"Area: {m2:.3f} m2", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(img_x)
    pdf.cell(60, 5, f"Subtotal: {subtotal:,.1f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(img_x)
    pdf.cell(60, 5, f"Price/m2: {gm2:,.1f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(img_x)
    pdf.cell(60, 5, f"Discount ({discount_pct}%): {discount_amount:,.1f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(img_x)
    pdf.cell(60, 5, f"After discount: {after_discount:,.1f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_x(img_x)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(60, 6, f"Final quote: {final_quote:,.0f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())


def generate_gate_info_pdf(
    items_df: pd.DataFrame,
    length: float,
    height: float,
    colour: str,
    chaps: int,
    motor: str,
) -> bytes:
    from fpdf.enums import XPos, YPos

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    today = date.today().strftime("%Y-%m-%d")

    page_w = pdf.w - pdf.l_margin - pdf.r_margin

    # Date top-right
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(pdf.w - pdf.r_margin - 40, pdf.t_margin)
    pdf.cell(40, 6, today, align="R")

    # Table on the left, slightly down
    table_x = pdf.l_margin
    table_top_y = pdf.t_margin + 4
    pdf.set_y(table_top_y)

    active = items_df[items_df["Quantity"] != 0].copy()

    col_widths = [50, 22, 20]
    headers = ["Item", "Size", "Qty"]
    row_h = 5.5
    font_size = 9

    pdf.set_font("Helvetica", "B", font_size)
    pdf.set_x(table_x)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, row_h + 1, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", font_size)
    for _, row in active.iterrows():
        size_str = f"{row['Size']:.2f}" if pd.notna(row["Size"]) else "-"
        vals = [
            str(row["Item"]),
            size_str,
            str(int(row["Quantity"])),
        ]
        pdf.set_x(table_x)
        for w, v in zip(col_widths, vals):
            pdf.cell(w, row_h, v, border=1, align="R" if v.replace(",", "").replace(".", "").isdigit() else "L")
        pdf.ln()

    # Image + info to the right of table
    img_x = table_x + sum(col_widths) + 10
    img_top_y = table_top_y
    _draw_gate_info_block(pdf, img_x, img_top_y, length, height, colour, chaps, motor)

    return bytes(pdf.output())


if "gate_items" not in st.session_state:
    st.session_state.gate_items = default_df()
    recalculate_from_inputs()
    # Apply default motor and adaptor selections
    select_motor("Motor 50N")
    select_adaptor("Adaptor 1 (Vali Glux)")

# ---------------------------------------------------------------------------
# TOP INPUTS — Height, Length, Chaps, Paleti Laynq, Motor, Adaptor, Discount
# ---------------------------------------------------------------------------
r1c1, r1c2, r1c3, r1c4 = st.columns(4)
with r1c1:
    height = st.number_input(
        "Height / Bardzrutyun (m)",
        value=0.3, step=0.01, format="%.2f",
        key="input_height",
        on_change=recalculate_from_inputs,
    )
with r1c2:
    length = st.number_input(
        "Length / Erakrutyun (m)",
        value=3.61, step=0.01, format="%.2f",
        key="input_length",
        on_change=recalculate_from_inputs,
    )
with r1c3:
    chaps = st.selectbox(
        "Chaps",
        [30, 35, 40],
        key="input_chaps",
        on_change=recalculate_from_inputs,
    )
with r1c4:
    paleti_laynq = st.number_input(
        "Paleti Laynq",
        value=0.077, step=0.001, format="%.3f",
        key="input_paleti_laynq",
        on_change=recalculate_from_inputs,
    )

r2c1, r2c2, r2c3, r2c4 = st.columns(4)
with r2c1:
    items_df = st.session_state.gate_items
    motor_idx = 0
    for i, name in enumerate(MOTOR_ITEMS):
        row = items_df.loc[items_df["Item"] == name]
        if len(row) > 0 and row.iloc[0]["Quantity"] > 0:
            motor_idx = i
            break
    st.selectbox(
        "Motor", MOTOR_ITEMS, index=motor_idx, key="motor_selector",
        on_change=lambda: select_motor(st.session_state.motor_selector),
    )
with r2c2:
    adap_idx = 0
    for i, name in enumerate(ADAPTOR_ITEMS):
        row = items_df.loc[items_df["Item"] == name]
        if len(row) > 0 and row.iloc[0]["Quantity"] > 0:
            adap_idx = i
            break
    st.selectbox(
        "Adaptor (Vali Glux)", ADAPTOR_ITEMS, index=adap_idx, key="adaptor_selector",
        on_change=lambda: select_adaptor(st.session_state.adaptor_selector),
    )
with r2c3:
    colour = st.selectbox(
        "Colour",
        ["Andracid", "Chocolate", "Metallic"],
        key="input_colour",
    )
with r2c4:
    discount_pct = st.number_input(
        "Discount % (\u0536\u0565\u0572\u057b\u057b)",
        value=10.0, step=0.5, format="%.1f",
    )

# ---------------------------------------------------------------------------
# EDIT — select an active item (use_size=True, Quantity > 0) and edit
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Edit")

edit_df = st.session_state.gate_items
edit_candidates = edit_df[
    (edit_df["use_size"] == True) & (edit_df["Quantity"] > 0)
]["Item"].tolist()

if not edit_candidates:
    st.info("No items with Chaps enabled and Quantity > 0.")
else:
    edit_col1, edit_col2 = st.columns([1, 5])
    with edit_col1:
        edit_selected = st.selectbox(
            "Apranq",
            edit_candidates,
            key="edit_selected",
        )

    edit_row = edit_df.loc[edit_df["Item"] == edit_selected].iloc[0]

    ef1, ef2, ef3, ef4, ef5 = st.columns(5)
    with ef1:
        st.number_input(
            "Chaps",
            value=float(edit_row["Size"]) if pd.notna(edit_row["Size"]) else 0.0,
            step=0.01, format="%.2f", min_value=0.0,
            key=f"edit_Size_{edit_selected}",
            on_change=apply_edit,
        )
    with ef2:
        st.number_input(
            "Qanak",
            value=int(edit_row["Quantity"]),
            step=1, format="%d", min_value=0,
            key=f"edit_Qty_{edit_selected}",
            on_change=apply_edit,
        )
    with ef3:
        st.number_input(
            "Gin",
            value=int(edit_row["Gin"]),
            step=100, format="%d", min_value=0,
            key=f"edit_Gin_{edit_selected}",
            on_change=apply_edit,
        )
    with ef4:
        st.checkbox(
            "Chapsov Hashvel",
            value=bool(edit_row["use_size"]),
            key=f"edit_use_{edit_selected}",
            on_change=apply_edit,
        )
    with ef5:
        st.write("")
        st.write("")
        if st.button("Hastatel", key="edit_apply"):
            apply_edit()
            st.toast(f"Updated {edit_selected}")

# ---------------------------------------------------------------------------
# COMPUTE SUMMARY
# ---------------------------------------------------------------------------
items_df = st.session_state.gate_items
m2 = length * height
subtotal = items_df["Total"].sum()
gm2 = subtotal / m2 if m2 else 0
discount_amount = subtotal * (discount_pct / 100)
after_discount = subtotal - discount_amount
final_quote = math.ceil(after_discount / 1000) * 1000

# ---------------------------------------------------------------------------
# FINAL QUOTE
# ---------------------------------------------------------------------------
left_sp, center, right_sp = st.columns([2, 3, 2])
with center:
    st.metric(
        label="Final quote / Verjnakan gin (\u054e\u0565\u0580\u057b\u056b\u0576\u0561\u056f\u0561\u0576 \u0563\u056b\u0576)",
        value=f"{final_quote:,.0f}",
        help="Rounded UP to nearest 1000. e.g. 315,057 -> 316,000",
    )

# ---------------------------------------------------------------------------
# ITEMS TABLE
# ---------------------------------------------------------------------------
st.subheader("Items / Apranqner (\u0531\u057a\u0580\u0561\u0576\u0584\u0576\u0565\u0580)")

df_display = items_df[["Type", "Item", "Size", "Quantity", "Gin", "Total", "use_size", "Mismatch"]].copy()

edited = st.data_editor(
    df_display,
    column_config={
        "Type":     st.column_config.TextColumn("Type", width="small"),
        "Item":     st.column_config.TextColumn("Item / Apranq", width="medium"),
        "Size":     st.column_config.NumberColumn("Chaps", format="%.2f", min_value=0, width="small"),
        "Quantity": st.column_config.NumberColumn("Qanak", format="%.0f", min_value=0, width="small"),
        "Gin":      st.column_config.NumberColumn("Gin (\u0533\u056b\u0576)", format="%.0f", min_value=0, width="medium"),
        "Total":    st.column_config.NumberColumn("Total", format="%.1f", width="medium"),
        "use_size": st.column_config.CheckboxColumn("Chapsov Hashvel", width="small"),
        "Mismatch": st.column_config.CheckboxColumn("!", width="small"),
    },
    disabled=["Type", "Item", "Total", "Mismatch"],
    use_container_width=True,
    key="editor",
)

if edited is not None:
    new_df = pd.DataFrame({
        "Type":     edited["Type"],
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
    r1b.metric("Subtotal / Yndhanur", f"{subtotal:,.1f}")
    r1c.metric("G/m\u00b2 / Gin (\u0533\u056b\u0576)", f"{gm2:,.1f}")
    r1d.metric("Discount / Zeghj (\u0536\u0565\u0572\u057b)", f"{discount_amount:,.1f}")

    r2a, r2b = st.columns(2)
    r2a.metric("After discount (\u0536\u0565\u0572\u057b\u056b\u0581 \u0570\u0565\u057f\u0578)", f"{after_discount:,.1f}")
    r2b.metric("Final quote (\u054e\u0565\u0580\u057b\u0576\u0561\u056f\u0561\u0576 \u0563\u056b\u0576)", f"{final_quote:,.0f}")

with reset_side:
    st.write("")
    st.write("")
    st.write("")
    if st.button("Reset to defaults", use_container_width=True):
        st.session_state.gate_items = default_df()
        recalculate_from_inputs()
        st.rerun()

    # Get motor name for PDF
    motor_name = ""
    for name in MOTOR_ITEMS:
        row = items_df.loc[items_df["Item"] == name]
        if len(row) > 0 and row.iloc[0]["Quantity"] > 0:
            motor_name = name
            break

    today_str = date.today().strftime("%Y_%m_%d")

    pdf_bytes = generate_pdf(
        items_df=items_df,
        discount_pct=discount_pct,
        m2=m2,
        subtotal=subtotal,
        gm2=gm2,
        discount_amount=discount_amount,
        after_discount=after_discount,
        final_quote=final_quote,
        length=length,
        height=height,
        colour=colour,
        chaps=chaps,
        motor=motor_name,
    )
    st.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name=f"gnarajark{today_str}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    gate_info_bytes = generate_gate_info_pdf(
        items_df=items_df,
        length=length,
        height=height,
        colour=colour,
        chaps=chaps,
        motor=motor_name,
    )
    st.download_button(
        label="Gate Info",
        data=gate_info_bytes,
        file_name=f"gate_info_{today_str}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

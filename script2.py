from typing import Any

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
import io

st.set_page_config(page_title="GST Invoice Generator", page_icon="🧾", layout="wide")

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background: #f8fafc; }
    .header { background: #1e293b; color: white; padding: 20px 24px; border-radius: 10px; margin-bottom: 20px; }
    .section { background: white; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 16px; }
    .stButton>button { background: #2563eb; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; width: 100%; }
    .stButton>button:hover { background: #1d4ed8; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="header"><h2 style="margin:0">🧾 GST Invoice Generator</h2><p style="margin:4px 0 0; color:#94a3b8">Generate professional GST-compliant invoices instantly</p></div>',
    unsafe_allow_html=True)


# ── PDF Generator ─────────────────────────────────────────────────────────────
def generate_invoice_pdf(seller, buyer, items, invoice_no, invoice_date, gst_type):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm)

    BLUE = colors.HexColor('#2563EB')
    DARK = colors.HexColor('#1E293B')
    LIGHT = colors.HexColor('#F1F5F9')
    MID = colors.HexColor('#475569')
    WHITE = colors.white
    W = A4[0] - 30 * mm

    def sty(name, **kw):
        base = dict(fontName='Helvetica', fontSize=9, textColor=MID, leading=13)
        base.update(kw)
        return ParagraphStyle(name, **base)

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    hdr = Table([[
        Paragraph(f"<font size=18 color='white'><b>{seller['name']}</b></font>", sty('h')),
        Paragraph("<font size=14 color='white'><b>TAX INVOICE</b></font>", sty('hr', alignment=TA_RIGHT))
    ]], colWidths=[W * 0.6, W * 0.4])
    hdr.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(hdr)

    # ── Seller / Invoice Info ─────────────────────────────────────────────────
    seller_text = (
        f"{seller['address']}<br/>"
        f"GSTIN: <b>{seller['gstin']}</b><br/>"
        f"Phone: {seller['phone']}<br/>"
        f"Email: {seller['email']}"
    )
    inv_text = (
        f"Invoice No: <b>{invoice_no}</b><br/>"
        f"Date: <b>{invoice_date}</b><br/>"
        f"GST Type: <b>{gst_type}</b>"
    )
    info = Table([[
        Paragraph(seller_text, sty('s')),
        Paragraph(inv_text, sty('i', alignment=TA_RIGHT))
    ]], colWidths=[W * 0.6, W * 0.4])
    info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(info)
    story.append(Spacer(1, 4 * mm))

    # ── Bill To ───────────────────────────────────────────────────────────────
    bill = Table([[
        Paragraph("<b>BILL TO</b>", sty('bt', textColor=BLUE)),
        ''
    ]], colWidths=[W * 0.5, W * 0.5])
    bill.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
    ]))
    story.append(bill)

    buyer_text = (
        f"<b>{buyer['name']}</b><br/>"
        f"{buyer['address']}<br/>"
        f"GSTIN: {buyer['gstin']}<br/>"
        f"Phone: {buyer['phone']}"
    )
    bill2 = Table([[Paragraph(buyer_text, sty('b2'))]], colWidths=[W])
    bill2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
    ]))
    story.append(bill2)
    story.append(Spacer(1, 4 * mm))

    # ── Items Table ───────────────────────────────────────────────────────────
    col_w = [W * 0.05, W * 0.30, W * 0.08, W * 0.10, W * 0.10, W * 0.08, W * 0.07, W * 0.07, W * 0.15]

    if gst_type == "IGST":
        headers = ['#', 'Description', 'HSN', 'Qty', 'Unit Price', 'Taxable', 'IGST%', 'IGST Amt', 'Total']
    else:
        headers = ['#', 'Description', 'HSN', 'Qty', 'Unit Price', 'Taxable', 'GST%', 'GST Amt', 'Total']

    rows = [[Paragraph(f"<b>{h}</b>", sty(f'h{i}', textColor=WHITE, alignment=TA_CENTER))
             for i, h in enumerate(headers)]]

    subtotal = cgst_total = sgst_total = igst_total = grand_total = 0

    for idx, item in enumerate(items, 1):
        qty = item['qty']
        unit_price = item['unit_price']
        taxable = qty * unit_price
        gst_rate = item['gst_rate']
        gst_amt = taxable * gst_rate / 100
        total = taxable + gst_amt

        subtotal += taxable
        igst_total += gst_amt
        grand_total += total

        if gst_type != "IGST":
            cgst_total += gst_amt / 2
            sgst_total += gst_amt / 2

        def c(v, align=TA_CENTER):
            return Paragraph(str(v), sty(f'c{idx}', alignment=align))

        rows.append([
            c(idx),
            c(item['desc'], TA_LEFT),
            c(item['hsn']),
            c(qty),
            c(f"Rs.{unit_price:,.2f}"),
            c(f"Rs.{taxable:,.2f}"),
            c(f"{gst_rate}%"),
            c(f"Rs.{gst_amt:,.2f}"),
            c(f"Rs.{total:,.2f}"),
        ])

    items_tbl = Table(rows, colWidths=col_w)
    items_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(items_tbl)
    story.append(Spacer(1, 4 * mm))

    # ── Totals ────────────────────────────────────────────────────────────────
    def row(label, value, bold=False):
        ls = sty('tl', alignment=TA_RIGHT, textColor=DARK)
        vs = sty('tv', alignment=TA_RIGHT, textColor=DARK)
        if bold:
            ls = sty('tlb', alignment=TA_RIGHT, textColor=WHITE, fontName='Helvetica-Bold')
            vs = sty('tvb', alignment=TA_RIGHT, textColor=WHITE, fontName='Helvetica-Bold')
        return [Paragraph(label, ls), Paragraph(value, vs)]

    total_rows = [row("Subtotal (Taxable):", f"Rs.{subtotal:,.2f}")]

    if gst_type == "IGST":
        total_rows.append(row("IGST:", f"Rs.{igst_total:,.2f}"))
    else:
        total_rows.append(row("CGST:", f"Rs.{cgst_total:,.2f}"))
        total_rows.append(row("SGST:", f"Rs.{sgst_total:,.2f}"))

    total_rows.append(row("GRAND TOTAL:", f"Rs.{grand_total:,.2f}", bold=True))

    totals_tbl = Table(total_rows, colWidths=[W * 0.8, W * 0.2])
    style = [
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('LINEABOVE', (0, -1), (-1, -1), 1, BLUE),
        ('BACKGROUND', (0, -1), (-1, -1), BLUE),
    ]
    totals_tbl.setStyle(TableStyle(style))
    story.append(totals_tbl)
    story.append(Spacer(1, 6 * mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1')))
    story.append(Spacer(1, 3 * mm))
    footer_data = [[
        Paragraph("Thank you for your business!", sty('f1', textColor=MID)),
        Paragraph(f"Authorised Signatory<br/><br/><br/>________________<br/>{seller['name']}",
                  sty('f2', alignment=TA_RIGHT, textColor=DARK))
    ]]
    footer = Table(footer_data, colWidths=[W * 0.6, W * 0.4])
    footer.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(footer)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ── UI ────────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🏢 Seller Details")
    s_name = st.text_input("Business Name", "Your Business Name")
    s_gstin = st.text_input("GSTIN", "27AAAAA0000A1Z5")
    s_address = st.text_input("Address", "123 Main St, Mumbai, Maharashtra")
    s_phone = st.text_input("Phone", "+91 98765 43210")
    s_email = st.text_input("Email", "you@business.com")

with col2:
    st.markdown("### 👤 Buyer Details")
    b_name = st.text_input("Buyer Name", "Client Business Name")
    b_gstin = st.text_input("Buyer GSTIN", "29BBBBB0000B1Z1")
    b_address = st.text_input("Buyer Address", "456 Park Ave, Bangalore, Karnataka")
    b_phone = st.text_input("Buyer Phone", "+91 98765 00000")

st.markdown("---")

col3, col4, col5 = st.columns(3)
with col3:
    invoice_no = st.text_input("Invoice Number", f"INV-{datetime.now().strftime('%Y%m')}-001")
with col4:
    invoice_date = st.date_input("Invoice Date", datetime.today())
with col5:
    gst_type = st.selectbox("GST Type", ["CGST + SGST (Intra-state)", "IGST (Inter-state)"])
    gst_type = "IGST" if "IGST" in gst_type else "CGST+SGST"

st.markdown("---")
st.markdown("### 📦 Items")

if 'invoice_items' not in st.session_state:
    st.session_state.invoice_items: list[Any] = []
for i, item in enumerate(st.session_state.invoice_items):
    c1, c2, c3, c4, c5, c6 = st.columns([3, 1.2, 1, 1.5, 1, 0.5])
    item['desc'] = c1.text_input("Description", item['desc'], key=f"desc_{i}")
    item['hsn'] = c2.text_input("HSN Code", item['hsn'], key=f"hsn_{i}")
    item['qty'] = c3.number_input("Qty", value=item['qty'], key=f"qty_{i}", min_value=1)
    item['unit_price'] = c4.number_input("Unit Price", value=item['unit_price'], key=f"up_{i}", min_value=0.0)
    item['gst_rate'] = c5.selectbox("GST%", [0, 5, 12, 18, 28], key=f"gst_{i}",
                                    index=[0, 5, 12, 18, 28].index(item['gst_rate']) if item['gst_rate'] in [0, 5, 12,
                                                                                                             18,
                                                                                                             28] else 3)
    if c6.button("❌", key=f"del_{i}") and len(st.session_state.items) > 1:
        st.session_state.invoice_items.pop(i)
        st.rerun()

if st.button("➕ Add Item"):
    st.session_state.invoice_items.append(
        {'desc': 'New Item', 'hsn': '000000', 'qty': 1, 'unit_price': 0.0, 'gst_rate': 18}
    )
    st.rerun()

# ── Live Total Preview ────────────────────────────────────────────────────────
st.markdown("---")
subtotal = sum(i['qty'] * i['unit_price'] for i in st.session_state.invoice_items)
tax = sum(i['qty'] * i['unit_price'] * i['gst_rate'] / 100 for i in st.session_state.invoice_items)
grand = subtotal + tax

m1, m2, m3 = st.columns(3)
m1.metric("Subtotal", f"Rs.{subtotal:,.2f}")
m2.metric("Total Tax", f"Rs.{tax:,.2f}")
m3.metric("Grand Total", f"Rs.{grand:,.2f}")

st.markdown("---")

if st.button("🧾 Generate GST Invoice PDF"):
    seller = dict(name=s_name, gstin=s_gstin, address=s_address, phone=s_phone, email=s_email)
    buyer = dict(name=b_name, gstin=b_gstin, address=b_address, phone=b_phone)

    with st.spinner("Generating invoice..."):
        pdf_buffer = generate_invoice_pdf(
            seller, buyer,
            st.session_state.items,
            invoice_no,
            invoice_date.strftime("%d-%m-%Y"),
            gst_type
        )

    st.success("Invoice generated!")
    st.download_button(
        label="⬇️ Download Invoice PDF",
        data=pdf_buffer,
        file_name=f"{invoice_no}.pdf",
        mime="application/pdf"
    )


# This is a sample Python script.

# Press Ctrl+F5 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.



# See PyCharm help at https://www.jetbrains.com/help/pycharm/

"""
Fatura Servisi - PDF oluşturma ve e-fatura entegrasyonları
"""
import os
import io
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models.invoice import (
    Invoice, InvoiceItem, InvoiceSettings, InvoiceProvider, InvoiceStatus, CompanyInfo
)

logger = logging.getLogger(__name__)


class InvoiceService:
    """Fatura servisi"""
    
    def __init__(self, settings: InvoiceSettings):
        self.settings = settings
    
    async def create_invoice(
        self,
        transaction: Dict[str, Any],
        user: Dict[str, Any],
        db,
        customer_name: Optional[str] = None,
        customer_address: Optional[str] = None,
        customer_tax_office: Optional[str] = None,
        customer_tax_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Invoice:
        """Fatura oluştur"""
        
        # Fatura numarası oluştur
        invoice_number = f"{self.settings.invoice_prefix}-{datetime.now().year}-{self.settings.next_invoice_number:04d}"
        
        # Fatura numarasını artır
        await db.invoice_settings.update_one(
            {"id": "invoice_settings"},
            {"$inc": {"next_invoice_number": 1}},
            upsert=True
        )
        
        # Fatura kalemi oluştur
        item = InvoiceItem(
            description=f"{transaction.get('package_name', 'Kredi Paketi')} - {transaction.get('credits_to_add', 0)} Kredi",
            quantity=1,
            unit_price=transaction.get('amount', 0),
            tax_rate=20.0
        )
        item.calculate_total()
        
        # Fatura oluştur
        invoice = Invoice(
            invoice_number=invoice_number,
            transaction_id=transaction.get('id', ''),
            user_id=user.get('id', ''),
            user_email=user.get('email', ''),
            customer_name=customer_name or user.get('full_name', 'Müşteri'),
            customer_email=user.get('email', ''),
            customer_address=customer_address,
            customer_tax_office=customer_tax_office,
            customer_tax_number=customer_tax_number,
            items=[item],
            currency=transaction.get('currency', 'TRY'),
            provider=self.settings.active_provider,
            notes=notes
        )
        invoice.calculate_totals()
        
        # PDF oluştur
        pdf_path = await self.generate_pdf(invoice)
        invoice.pdf_url = pdf_path
        
        # Veritabanına kaydet
        invoice_dict = invoice.model_dump()
        invoice_dict['created_at'] = invoice_dict['created_at'].isoformat() if isinstance(invoice_dict['created_at'], datetime) else invoice_dict['created_at']
        await db.invoices.insert_one(invoice_dict)
        
        logger.info(f"Invoice created: {invoice_number} for {user.get('email')}")
        
        # E-fatura gönder (eğer aktif ise)
        if self.settings.active_provider != InvoiceProvider.MANUAL:
            await self.send_to_provider(invoice)
        
        return invoice
    
    async def generate_pdf(self, invoice: Invoice) -> str:
        """PDF fatura oluştur"""
        
        # PDF dosya yolu
        filename = f"invoice_{invoice.invoice_number.replace('-', '_')}.pdf"
        filepath = f"/tmp/{filename}"
        
        # PDF oluştur
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Başlık stili
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=1
        )
        
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            spaceAfter=5
        )
        
        # Şirket başlığı
        company = self.settings.company
        story.append(Paragraph(company.company_name, title_style))
        story.append(Spacer(1, 10))
        
        # Şirket ve fatura bilgileri tablosu
        company_info = [
            [Paragraph(f"<b>Satıcı Bilgileri</b>", styles['Heading3']), 
             Paragraph(f"<b>Fatura Bilgileri</b>", styles['Heading3'])],
            [Paragraph(f"{company.company_name}<br/>{company.address}<br/>Tel: {company.phone}<br/>Email: {company.email}<br/>Vergi Dairesi: {company.tax_office}<br/>Vergi No: {company.tax_number}", header_style),
             Paragraph(f"<b>Fatura No:</b> {invoice.invoice_number}<br/><b>Tarih:</b> {invoice.created_at.strftime('%d.%m.%Y')}<br/><b>Para Birimi:</b> {invoice.currency}", header_style)]
        ]
        
        company_table = Table(company_info, colWidths=[9*cm, 8*cm])
        company_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(company_table)
        story.append(Spacer(1, 20))
        
        # Müşteri bilgileri
        customer_info = [
            [Paragraph(f"<b>Müşteri Bilgileri</b>", styles['Heading3'])],
            [Paragraph(f"<b>Ad Soyad:</b> {invoice.customer_name}<br/><b>Email:</b> {invoice.customer_email}" + 
                      (f"<br/><b>Adres:</b> {invoice.customer_address}" if invoice.customer_address else "") +
                      (f"<br/><b>Vergi Dairesi:</b> {invoice.customer_tax_office}" if invoice.customer_tax_office else "") +
                      (f"<br/><b>Vergi No:</b> {invoice.customer_tax_number}" if invoice.customer_tax_number else ""), 
                      header_style)]
        ]
        customer_table = Table(customer_info, colWidths=[17*cm])
        customer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(customer_table)
        story.append(Spacer(1, 20))
        
        # Fatura kalemleri tablosu
        items_data = [
            [Paragraph('<b>Açıklama</b>', styles['Normal']),
             Paragraph('<b>Miktar</b>', styles['Normal']),
             Paragraph('<b>Birim Fiyat</b>', styles['Normal']),
             Paragraph('<b>KDV %</b>', styles['Normal']),
             Paragraph('<b>Toplam</b>', styles['Normal'])]
        ]
        
        currency_symbols = {'TRY': '₺', 'USD': '$', 'EUR': '€'}
        symbol = currency_symbols.get(invoice.currency, invoice.currency)
        
        for item in invoice.items:
            items_data.append([
                Paragraph(item.description, styles['Normal']),
                str(item.quantity),
                f"{symbol}{item.unit_price:.2f}",
                f"%{item.tax_rate:.0f}",
                f"{symbol}{item.total:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[8*cm, 2*cm, 2.5*cm, 2*cm, 2.5*cm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Toplam tablosu
        totals_data = [
            ['Ara Toplam:', f"{symbol}{invoice.subtotal:.2f}"],
            ['KDV (%20):', f"{symbol}{invoice.tax_amount:.2f}"],
            ['Genel Toplam:', f"{symbol}{invoice.total_amount:.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[13*cm, 4*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 30))
        
        # Notlar
        if invoice.notes:
            story.append(Paragraph(f"<b>Notlar:</b> {invoice.notes}", header_style))
            story.append(Spacer(1, 20))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#6b7280'),
            alignment=1
        )
        story.append(Spacer(1, 40))
        story.append(Paragraph(f"Bu fatura elektronik ortamda oluşturulmuştur.", footer_style))
        story.append(Paragraph(f"{company.website}", footer_style))
        
        # PDF'i oluştur
        doc.build(story)
        
        logger.info(f"PDF invoice generated: {filepath}")
        return filepath
    
    async def send_to_provider(self, invoice: Invoice) -> bool:
        """E-fatura sağlayıcısına gönder"""
        
        try:
            if self.settings.active_provider == InvoiceProvider.PARASUT:
                return await self._send_to_parasut(invoice)
            elif self.settings.active_provider == InvoiceProvider.BIZIMHESAP:
                return await self._send_to_bizimhesap(invoice)
            elif self.settings.active_provider == InvoiceProvider.BIRFATURA:
                return await self._send_to_birfatura(invoice)
            else:
                return True
        except Exception as e:
            logger.error(f"E-fatura gönderimi başarısız: {str(e)}")
            return False
    
    async def _send_to_parasut(self, invoice: Invoice) -> bool:
        """Paraşüt'e fatura gönder"""
        # TODO: Paraşüt API entegrasyonu
        # https://apidocs.parasut.com/
        logger.info(f"Paraşüt'e fatura gönderilecek: {invoice.invoice_number}")
        
        if not self.settings.parasut_client_id or not self.settings.parasut_client_secret:
            logger.warning("Paraşüt API bilgileri eksik")
            return False
        
        # API çağrısı yapılacak
        return True
    
    async def _send_to_bizimhesap(self, invoice: Invoice) -> bool:
        """Bizimhesap'a fatura gönder"""
        # TODO: Bizimhesap API entegrasyonu
        logger.info(f"Bizimhesap'a fatura gönderilecek: {invoice.invoice_number}")
        
        if not self.settings.bizimhesap_api_key:
            logger.warning("Bizimhesap API bilgileri eksik")
            return False
        
        return True
    
    async def _send_to_birfatura(self, invoice: Invoice) -> bool:
        """Birfatura'ya fatura gönder"""
        # TODO: Birfatura API entegrasyonu
        logger.info(f"Birfatura'ya fatura gönderilecek: {invoice.invoice_number}")
        
        if not self.settings.birfatura_api_key:
            logger.warning("Birfatura API bilgileri eksik")
            return False
        
        return True


async def get_invoice_settings(db) -> InvoiceSettings:
    """Fatura ayarlarını al"""
    settings = await db.invoice_settings.find_one({"id": "invoice_settings"}, {"_id": 0})
    
    if settings:
        return InvoiceSettings(**settings)
    
    # Varsayılan ayarlar
    default_settings = InvoiceSettings()
    await db.invoice_settings.insert_one(default_settings.model_dump())
    return default_settings

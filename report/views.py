from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Q
from django.db.models.functions import TruncHour
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from entrances.models import Entrance
from people.models import People


def _build_pdf(period, title, summary_rows, recent_entrances, people_rows):
	buffer = BytesIO()
	doc = SimpleDocTemplate(
		buffer,
		pagesize=A4,
		leftMargin=16 * mm,
		rightMargin=16 * mm,
		topMargin=16 * mm,
		bottomMargin=16 * mm,
		title=title,
		author="Smart Scan",
	)

	styles = getSampleStyleSheet()
	title_style = ParagraphStyle(
		"ReportTitle",
		parent=styles["Title"],
		fontName="Helvetica-Bold",
		fontSize=20,
		leading=24,
		textColor=colors.HexColor("#111827"),
		spaceAfter=4,
	)
	subtitle_style = ParagraphStyle(
		"ReportSubtitle",
		parent=styles["Normal"],
		fontName="Helvetica",
		fontSize=9,
		leading=12,
		textColor=colors.HexColor("#6B7280"),
		spaceAfter=10,
	)
	section_style = ParagraphStyle(
		"SectionHeader",
		parent=styles["Heading2"],
		fontName="Helvetica-Bold",
		fontSize=12,
		leading=14,
		textColor=colors.HexColor("#111827"),
		spaceBefore=8,
		spaceAfter=6,
	)
	small_style = ParagraphStyle(
		"SmallBody",
		parent=styles["Normal"],
		fontName="Helvetica",
		fontSize=8.5,
		leading=11,
		textColor=colors.HexColor("#374151"),
	)

	total_people = len(people_rows)
	active_people = sum(1 for row in people_rows if row["entrance_count"] > 0)

	story = [
		Paragraph(title, title_style),
		Paragraph(
			f"Generated at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} | Period: {period.title()}",
			subtitle_style,
		),
	]

	kpi_table = Table(
		[[
			Paragraph("Selected Period Total", small_style),
			Paragraph("Total People", small_style),
			Paragraph("Active People", small_style),
		], [
			Paragraph(f"<b>{len(summary_rows) and sum(row['value'] for row in summary_rows) or 0}</b>", title_style),
			Paragraph(f"<b>{total_people}</b>", title_style),
			Paragraph(f"<b>{active_people}</b>", title_style),
		]],
		colWidths=[55 * mm, 55 * mm, 55 * mm],
	)
	kpi_table.setStyle(
		TableStyle(
			[
				("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
				("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F9FAFB")),
				("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
				("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D1D5DB")),
				("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
				("ALIGN", (0, 0), (-1, -1), "CENTER"),
				("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
				("BOTTOMPADDING", (0, 0), (-1, -1), 8),
				("TOPPADDING", (0, 0), (-1, -1), 8),
			]
		)
	)
	story.extend([kpi_table, Spacer(1, 8)])

	story.append(Paragraph("Summary Overview", section_style))
	if summary_rows:
		summary_data = [["Period", "Count"]] + [[row["label"], str(row["value"])] for row in summary_rows]
	else:
		summary_data = [["Period", "Count"], ["No records found", "-"]]
	summary_table = Table(summary_data, colWidths=[110 * mm, 30 * mm])
	summary_table.setStyle(
		TableStyle(
			[
				("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
				("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
				("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
				("FONTSIZE", (0, 0), (-1, -1), 9),
				("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
				("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D1D5DB")),
				("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#E5E7EB")),
				("ALIGN", (1, 1), (-1, -1), "CENTER"),
				("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
				("TOPPADDING", (0, 0), (-1, -1), 7),
				("BOTTOMPADDING", (0, 0), (-1, -1), 7),
			]
		)
	)
	story.append(summary_table)

	story.append(Paragraph("Record Logs", section_style))
	logs_data = [["Name", "Time", "Status"]]
	for entrance in recent_entrances[:25]:
		logs_data.append(
			[
				Paragraph(entrance.people.name, small_style),
				Paragraph(entrance.time.strftime("%Y-%m-%d %H:%M:%S"), small_style),
				Paragraph("Verified", small_style),
			]
		)
	if len(logs_data) == 1:
		logs_data.append(["No recent entries", "-", "-"])

	logs_table = Table(logs_data, colWidths=[65 * mm, 55 * mm, 25 * mm], repeatRows=1)
	logs_table.setStyle(
		TableStyle(
			[
				("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
				("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
				("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
				("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ECFDF5")]),
				("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#A7F3D0")),
				("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1FAE5")),
				("ALIGN", (2, 1), (2, -1), "CENTER"),
				("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
				("TOPPADDING", (0, 0), (-1, -1), 6),
				("BOTTOMPADDING", (0, 0), (-1, -1), 6),
			]
		)
	)
	story.append(logs_table)

	story.append(Paragraph("People Directory", section_style))
	people_data = [["Name", "NRC", "Father", "Entries", "Last Entry", "QR", "Address"]]
	for person in people_rows:
		people_data.append(
			[
				Paragraph(person["name"], small_style),
				Paragraph(person["nrc"], small_style),
				Paragraph(person["father_name"], small_style),
				Paragraph(str(person["entrance_count"]), small_style),
				Paragraph(person["last_entrance"].strftime("%Y-%m-%d %H:%M") if person["last_entrance"] else "-", small_style),
				Paragraph(person["qr_status"], small_style),
				Paragraph(person["address"], small_style),
			]
		)
	if len(people_data) == 1:
		people_data.append(["No people found", "-", "-", "-", "-", "-", "-"])

	people_table = Table(people_data, colWidths=[28 * mm, 28 * mm, 28 * mm, 14 * mm, 24 * mm, 18 * mm, 45 * mm], repeatRows=1)
	people_table.setStyle(
		TableStyle(
			[
				("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
				("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
				("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
				("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EFF6FF")]),
				("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#BFDBFE")),
				("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DBEAFE")),
				("VALIGN", (0, 0), (-1, -1), "TOP"),
				("ALIGN", (3, 1), (5, -1), "CENTER"),
				("TOPPADDING", (0, 0), (-1, -1), 6),
				("BOTTOMPADDING", (0, 0), (-1, -1), 6),
			]
		)
	)
	story.append(people_table)

	def add_page_number(canvas_obj, doc_obj):
		canvas_obj.setFont("Helvetica", 8)
		canvas_obj.setFillColor(colors.HexColor("#6B7280"))
		canvas_obj.drawRightString(doc_obj.pagesize[0] - doc_obj.rightMargin, 10 * mm, f"Page {doc_obj.page}")

	doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
	buffer.seek(0)
	return buffer


@login_required
def report_view(request):
	period = "daily"

	entrance_qs = Entrance.objects.select_related("people").order_by("-time")
	filtered_entrances = entrance_qs.filter(time__date=timezone.now().date())

	summary_rows = [
		{
			"label": row["period_key"].strftime("%H:00"),
			"value": row["total"],
		}
		for row in (
			Entrance.objects.annotate(period_key=TruncHour("time"))
			.filter(time__date=timezone.now().date())
			.values("period_key")
			.annotate(total=Count("entrance_id"))
			.order_by("period_key")
		)
	]

	total_entries = filtered_entrances.count()
	recent_entrances = filtered_entrances[:20]

	people_qs = (
		People.objects.annotate(
			entrance_count=Count("entrance", distinct=True),
			qr_count=Count("qr_codes", distinct=True),
			active_qr_count=Count(
				"qr_codes",
				filter=Q(qr_codes__is_active=True),
				distinct=True,
			),
			last_entrance=Max("entrance__time"),
		)
		.order_by("name")
	)

	people_rows = []
	for person in people_qs:
		people_rows.append(
			{
				"name": person.name,
				"nrc": person.nrc,
				"father_name": person.father_name,
				"address": person.address,
				"register_date": person.register_date,
				"picture": person.picture,
				"entrance_count": person.entrance_count,
				"qr_count": person.qr_count,
				"active_qr_count": person.active_qr_count,
				"last_entrance": person.last_entrance,
				"qr_status": "Active" if person.active_qr_count else "Inactive",
			}
		)

	if request.GET.get("format") == "pdf":
		title = "Daily Entrance Report"
		pdf_buffer = _build_pdf(period, title, summary_rows, recent_entrances, people_rows)
		response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
		response["Content-Disposition"] = 'attachment; filename="daily-entrance-report.pdf"'
		return response

	recent_rows = [
		{
			"name": entrance.people.name,
			"timestamp": entrance.time,
		}
		for entrance in recent_entrances
	]

	return render(
		request,
		"report/index.html",
		{
			"period": period,
			"report_title": "Daily Entrance Report",
			"total_entries": total_entries,
			"summary_rows": summary_rows,
			"recent_rows": recent_rows,
			"people_rows": people_rows,
			"total_people": len(people_rows),
			"active_people": sum(1 for row in people_rows if row["entrance_count"] > 0),
		},
	)

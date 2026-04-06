"""
MCP Tool : Génération Kit d'Entretien PDF
"""

import sys
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from mocks import enregistrer_trace_ats

async def creer_kit_entretien_tool(
    candidature_id: str,
    poste_id: str,
    interview_kit: dict,
    candidat_data: dict,
    poste_data: dict
) -> dict:
    """
    Génère un kit d'entretien PDF complet
    
    Args:
        candidature_id: ID de la candidature
        poste_id: ID du poste
        interview_kit: Kit généré par le LLM
        candidat_data: Données du candidat
        poste_data: Données du poste
    
    Returns:
        dict: Résultat avec chemin du PDF
    """
    
    try:
        # 1. Crée le dossier de sortie si nécessaire
        output_dir = os.path.join(parent_dir, "output_pdfs")
        os.makedirs(output_dir, exist_ok=True)
        
        # 2. Nom du fichier
        candidat_nom = f"{candidat_data.get('prenom', '')}_{candidat_data.get('nom', '')}".replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"KIT_ENTRETIEN_{candidat_nom}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        print(f"\n📄 [PDF] Génération du kit d'entretien...")
        print(f"   Fichier : {filename}")
        
        # 3. Crée le document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 4. Styles
        styles = getSampleStyleSheet()
        
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        style_heading = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        style_normal = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        style_bullet = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceAfter=4
        )
        
        # 5. Construction du contenu
        story = []
        
        # === EN-TÊTE ===
        story.append(Paragraph("KIT D'ENTRETIEN", style_title))
        story.append(Spacer(1, 0.5*cm))
        
        # Infos candidat et poste
        info_data = [
            ['Candidat', f"{candidat_data.get('prenom', '')} {candidat_data.get('nom', '')}"],
            ['Email', candidat_data.get('email', 'N/A')],
            ['Poste', poste_data.get('titre', 'N/A')],
            ['Date', datetime.now().strftime('%d/%m/%Y')]
        ]
        
        info_table = Table(info_data, colWidths=[4*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 1*cm))
        
        # === SECTION 1 : GRILLE D'ÉVALUATION ===
        story.append(Paragraph("1. GRILLE D'ÉVALUATION PONDÉRÉE", style_heading))
        story.append(Spacer(1, 0.3*cm))
        
        grille = interview_kit.get('grille_evaluation', [])
        
        if grille:
            grille_data = [['Compétence', 'Poids', 'Note /5']]
            
            for item in grille:
                grille_data.append([
                    item.get('competence', 'N/A'),
                    f"{item.get('poids', 0)}%",
                    '☐☐☐☐☐'
                ])
            
            grille_data.append(['SCORE TOTAL', '', '     /5'])
            
            grille_table = Table(grille_data, colWidths=[8*cm, 3*cm, 5*cm])
            grille_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#ECF0F1')),
                ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(grille_table)
        else:
            story.append(Paragraph("Aucune compétence définie.", style_normal))
        
        story.append(Spacer(1, 0.8*cm))
        
        # === SECTION 2 : QUESTIONS TECHNIQUES ===
        story.append(Paragraph("2. QUESTIONS TECHNIQUES", style_heading))
        story.append(Spacer(1, 0.3*cm))
        
        questions_tech = interview_kit.get('questions_techniques', [])
        
        if questions_tech:
            for i, q in enumerate(questions_tech, 1):
                competence = q.get('competence', 'Général')
                question = q.get('question', '')
                
                story.append(Paragraph(
                    f"<b>Q{i}. [{competence}]</b> {question}",
                    style_normal
                ))
                story.append(Spacer(1, 0.2*cm))
        else:
            story.append(Paragraph("Aucune question technique définie.", style_normal))
        
        story.append(Spacer(1, 0.8*cm))
        
        # === SECTION 3 : QUESTIONS COMPORTEMENTALES ===
        story.append(Paragraph("3. QUESTIONS COMPORTEMENTALES (Méthode STAR)", style_heading))
        story.append(Spacer(1, 0.3*cm))
        
        questions_comp = interview_kit.get('questions_comportementales', [])
        
        if questions_comp:
            for i, q in enumerate(questions_comp, 1):
                categorie = q.get('categorie', 'Général')
                question = q.get('question', '')
                
                story.append(Paragraph(
                    f"<b>Q{i}. [{categorie}]</b> {question}",
                    style_normal
                ))
                story.append(Spacer(1, 0.3*cm))
                story.append(Paragraph(
                    "→ <i>Situation</i> : ...",
                    style_bullet
                ))
                story.append(Paragraph(
                    "→ <i>Tâche</i> : ...",
                    style_bullet
                ))
                story.append(Paragraph(
                    "→ <i>Action</i> : ...",
                    style_bullet
                ))
                story.append(Paragraph(
                    "→ <i>Résultat</i> : ...",
                    style_bullet
                ))
                story.append(Spacer(1, 0.3*cm))
        else:
            story.append(Paragraph("Aucune question comportementale définie.", style_normal))
        
        story.append(PageBreak())
        
        # === SECTION 4 : CRITÈRES DE NOTATION ===
        story.append(Paragraph("4. CRITÈRES DE NOTATION", style_heading))
        story.append(Spacer(1, 0.3*cm))
        
        criteres = interview_kit.get('criteres_notation', {})
        
        if criteres:
            criteres_data = [['Note', 'Description']]
            
            for note in ['5', '4', '3', '2', '1']:
                if note in criteres:
                    criteres_data.append([
                        f"{note}/5",
                        criteres[note]
                    ])
            
            criteres_table = Table(criteres_data, colWidths=[2*cm, 14*cm])
            criteres_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            story.append(criteres_table)
        else:
            story.append(Paragraph("Aucun critère de notation défini.", style_normal))
        
        story.append(Spacer(1, 0.8*cm))
        
        # === SECTION 5 : POINTS D'ATTENTION ===
        story.append(Paragraph("5. POINTS D'ATTENTION SPÉCIFIQUES", style_heading))
        story.append(Spacer(1, 0.3*cm))
        
        points = interview_kit.get('points_attention', [])
        
        if points:
            for point in points:
                story.append(Paragraph(f"• {point}", style_bullet))
        else:
            story.append(Paragraph("Aucun point d'attention spécifique.", style_normal))
        
        story.append(Spacer(1, 1*cm))
        
        # Footer
        story.append(Spacer(1, 2*cm))
        story.append(Paragraph(
            f"<i>Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        ))
        
        # 6. Génère le PDF
        doc.build(story)
        
        print(f"   ✓ PDF généré avec succès")
        print(f"   Chemin : {filepath}")
        
        # 7. Enregistre trace ATS
        enregistrer_trace_ats({
            "type": "generation_kit_entretien",
            "candidat_id": candidat_data.get('id'),
            "date": datetime.now().isoformat(),
            "type_detail": f"Kit entretien généré pour {poste_data.get('titre')}"
        })
        
        # 8. Retourne résultat
        return {
            "status": "success",
            "candidature_id": candidature_id,
            "poste_id": poste_id,
            "pdf_path": filepath,
            "pdf_filename": filename,
            "sections": {
                "grille_evaluation": len(grille),
                "questions_techniques": len(questions_tech),
                "questions_comportementales": len(questions_comp),
                "criteres_notation": len(criteres),
                "points_attention": len(points)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"\n [PDF] Erreur : {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "error": str(e)
        }
from fpdf import FPDF
from datetime import datetime

class ScorecardPDF(FPDF):
    def header(self):
        # MentorMind AI Header
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(88, 166, 255) # primary blue
        self.cell(0, 10, 'MentorMind AI - Candidate Scorecard', 0, 1, 'C')
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(128, 128, 128)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(0, 10, f'Generated on: {date_str}', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_candidate_scorecard(candidate_name, profile, interview):
    pdf = ScorecardPDF()
    pdf.add_page()
    
    # Brand line
    pdf.set_draw_color(88, 166, 255)
    pdf.line(10, 35, 200, 35)
    pdf.ln(5)
    
    # Basic Details
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, 'Candidate Profile', 0, 1)
    
    pdf.set_font('helvetica', '', 12)
    pdf.cell(40, 8, 'Name:', 0, 0)
    pdf.cell(0, 8, str(candidate_name), 0, 1)
    
    pdf.cell(40, 8, 'Qualification:', 0, 0)
    pdf.cell(0, 8, str(profile.get('qualification', 'N/A')), 0, 1)
    
    pdf.cell(40, 8, 'Subjects:', 0, 0)
    pdf.cell(0, 8, str(profile.get('subjects', 'N/A')), 0, 1)
    
    pdf.cell(40, 8, 'Experience:', 0, 0)
    pdf.cell(0, 8, str(profile.get('experience', 'N/A')), 0, 1)
    pdf.ln(5)
    
    # Resume Insights
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, 'AI Resume Insights', 0, 1)
    pdf.set_font('helvetica', 'I', 11)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 6, str(profile.get('resume_summary', 'No summary provided.')))
    pdf.ln(8)
    
    # Interview Results
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, 'Interview Evaluation', 0, 1)
    
    pdf.set_font('helvetica', '', 12)
    pdf.cell(45, 8, 'Date:', 0, 0)
    pdf.cell(0, 8, str(interview.get('date', 'N/A')), 0, 1)
    
    pdf.cell(45, 8, 'Subject:', 0, 0)
    pdf.cell(0, 8, str(interview.get('subject', 'N/A')), 0, 1)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(45, 8, 'Final Verdict:', 0, 0)
    
    verdict = str(interview.get('verdict', 'N/A')).upper()
    if verdict == "SELECTED":
        pdf.set_text_color(0, 150, 0)
    elif verdict == "REJECTED":
        pdf.set_text_color(200, 0, 0)
    else:
        pdf.set_text_color(200, 150, 0)
        
    pdf.cell(0, 8, verdict, 0, 1)
    pdf.set_text_color(30, 30, 30)
    pdf.ln(5)
    
    # Scores
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, 'Specific Scores (/100):', 0, 1)
    pdf.set_font('helvetica', '', 11)
    
    # Helper to print scores
    def print_score(label, keys):
        score = 0
        for k in keys:
            val = interview.get(k)
            if val is None and 'scores' in interview:
                val = interview['scores'].get(k)
            if val is not None:
                try:
                    score = int(val)
                    break
                except: pass
        pdf.cell(60, 6, f"{label}:", 0, 0)
        pdf.cell(0, 6, f"{score}/100", 0, 1)
        return score
        
    s_l1 = print_score('L1 (Teaching Fundamentals)', ['l1_score'])
    s_l2 = print_score('L2 (Subject Knowledge)', ['l2_score'])
    s_cl = print_score('Clarity', ['clarity', 'score_clarity'])
    s_co = print_score('Communication', ['communication', 'score_communication'])
    s_ps = print_score('Problem Solving', ['problem_solving', 'simplicity', 'score_problem_solving'])
    s_sk = print_score('Subject Knowledge', ['subject_knowledge', 'subject', 'score_subject_knowledge'])
    s_ta = print_score('Teaching Ability', ['teaching_ability', 'patience', 'score_teaching_ability'])
    pdf.ln(5)
    
    # Generate Pie Chart image 
    try:
        import matplotlib.pyplot as plt
        import os
        labels = ['Clarity', 'Communication', 'Logic', 'Knowledge', 'Instructional']
        sizes = [s_cl, s_co, s_ps, s_sk, s_ta]
        # Only draw if there are some non-zero values
        if sum(sizes) > 0:
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.pie(sizes, labels=labels, autopct='%1.0f%%', startangle=140, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99', '#c2c2f0'])
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            chart_path = os.path.join(os.path.dirname(__file__), "temp_pie.png")
            fig.savefig(chart_path, transparent=True, bbox_inches='tight')
            plt.close(fig)
            if os.path.exists(chart_path):
                # Right align chart on the same Y axis
                pdf.image(chart_path, x=135, y=140, w=65)
                os.remove(chart_path)
    except:
        pass
    
    # Feedback
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, 'Detailed AI Feedback:', 0, 1)
    pdf.set_font('helvetica', '', 11)
    pdf.set_text_color(60, 60, 60)
    
    feedback_text = str(interview.get('feedback', interview.get('insights', 'No feedback provided.')))
    if 'strengths' in interview:
        feedback_text += "\n\nPoints of Excellence:\n" + "\n".join([f"- {s}" for s in interview['strengths']])
    if 'weaknesses' in interview:
        feedback_text += "\n\nDevelopment Vectors:\n" + "\n".join([f"- {w}" for w in interview['weaknesses']])

    # sanitize characters for latin-1 compatibility (FPDF default)
    feedback_text = feedback_text.replace('\u2013', '-').replace('\u2014', '-').replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    feedback_text = feedback_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, feedback_text)
    
    # Output byte array compatible with streamlit download button
    return bytes(pdf.output())

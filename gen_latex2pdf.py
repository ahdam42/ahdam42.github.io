from pdflatex import PDFLaTeX
import os


os.environ['PATH'] = os.environ['PATH'] + r';D:\programm\texlive\2025\bin\windows'

path2ltx = 'data/flattened_cnn/iclr2015.tex'
pdfl = PDFLaTeX.from_texfile(path2ltx)

print(pdfl)

pdf, log, completed_process = pdfl.create_pdf(keep_pdf_file=True, keep_log_file=True)

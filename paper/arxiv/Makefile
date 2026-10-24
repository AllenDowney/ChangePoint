LATEX = latex

DVIPS = dvips

PDFFLAGS = -dCompatibilityLevel=1.4 \
           -dCompressPages=true -dUseFlateCompression=true  \
           -dEmbedAllFonts=true -dSubsetFonts=true -dMaxSubsetPct=100

%.dvi: %.tex
	$(LATEX) $<

%.ps: %.dvi
	$(DVIPS) -Ppdf -G0 -o $@ $<

%.pdf: %.ps
	ps2pdf $(PDFFLAGS) $< $@

paper: paper.tex
	latex paper
	bibtex paper
	latex paper
	dvips -Ppdf -o paper.ps paper
	gv paper.ps
	ps2pdf $(PDFFLAGS) paper.ps downey08changepoint.pdf


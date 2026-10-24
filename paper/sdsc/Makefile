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

slides: slides.tex
	latex slides
	dvips -Ppdf -G0 -o slides.ps slides
	ps2pdf $(PDFFLAGS) slides.ps slides.pdf
	gv --orientation=landscape slides.ps

dist:
	cp paper.ps downey06changepoint.ps
	cp paper.bib downey06changepoint.bib
	gzip -c downey06changepoint.ps > downey06changepoint.ps.gz
	ps2pdf $(PDFFLAGS) paper.ps downey06changepoint.pdf
	cp slides.ps downey06changepoint.slides.ps
	gzip -c slides.ps > downey06changepoint.slides.ps.gz
	cp slides.pdf downey06changepoint.slides.pdf
	chmod 644 downey06changepoint.*
	cp downey06changepoint.* /home/downey/public_html/research/changepoint


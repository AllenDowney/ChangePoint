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

nup:
	psnup -l -b20 -6 slides.ps slides.6.ps

dist:
	cp paper.ps downey08changepoint.ps
	cp paper.bib downey08changepoint.bib
	gzip -c downey08changepoint.ps > downey08changepoint.ps.gz
	ps2pdf $(PDFFLAGS) paper.ps downey08changepoint.pdf
	cp slides.ps downey08changepoint.slides.ps
	gzip -c slides.ps > downey08changepoint.slides.ps.gz
	cp slides.pdf downey08changepoint.slides.pdf
	chmod 644 downey08changepoint.*
	cp downey08changepoint.* /home/downey/public_html/research/changepoint


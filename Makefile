all: fondrie_cv.pdf

%.pdf: %.tex
	pdflatex $*.tex
	if ( grep -q citation $*.aux ) ; then \
		bibtex $* ; \
		pdflatex $*.tex ; \
	fi
	pdflatex $*.tex

fondrie_cv.tex: fondrie_cv.template.tex build.py presentations.json pubs.bib
	python build.py

clean:
	rm -r *.aux *.log *.out auto/

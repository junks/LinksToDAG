
all:
	pdflatex LinksToDAG_final.tex && bibtex LinksToDAG_final.aux && pdflatex LinksToDAG_final.tex -output-format pdf -halt-on-error -file-line-error && pdflatex LinksToDAG.tex && bibtex LinksToDAG.aux && pdflatex LinksToDAG.tex --output-format pdf -halt-on-error -file-line-error && (pdftk LinksToDAG_final.pdf cat 1-13 output body.pdf; pdftk LinksToDAG.pdf cat 7-end output supplement.pdf; zip supplement.zip supplement.pdf) && echo "Now submit body.pdf and supplement.zip"

paper:
	bibtex LinksToDAG_final.aux && pdflatex LinksToDAG_final.tex -output-format pdf -halt-on-error -file-line-error

parses.pdf: figure/parses.tikz
	pdflatex parses.tex


clean:
	rm *.aux *.log
	rm *.blg 
	rm *.bbl


# Graphs
graph_runtime:
	python ../src/tools/plotter.py -x "Sentences" -y "Runtime (seconds)" -o "sol/runtimes/runtimes.png" ../sol/runtimes/runtimes.txt
	cp ../sol/runtimes/runtimes.png figure

graph_precision_recall:
	python ../src/tools/plotter.py -x Sentences -y Percent -o ../sol/precision_recall/precision_recall.png ../sol/precision_recall/precision.txt ../sol/precision_recall/recall.txt
	cp ../sol/precision_recall/precision_recall.png figure/

graphs: graph_precision_recall



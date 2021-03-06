#!/bin/sh

cd ..; make graph_precision_recall; cd doc;


if [ $1 ];
then
pdflatex $1 && bibtex *.aux && pdflatex $1 && pdflatex $1

else
pdflatex *.tex && bibtex *.aux && pdflatex *.tex && pdflatex *.tex
fi

./clean.sh

# Build PDF

`docker run --rm   --volume $PWD:/data   --user $(id -u):$(id -g)   openjournals/inara   -o pdf,crossref paper.md`

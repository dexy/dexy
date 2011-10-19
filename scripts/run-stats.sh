ohcount dexy > stats/dexy.count
ohcount tests > stats/tests.count
ohcount handlers > stats/filters.count
ohcount docs examples features > stats/docs.count

export REVNO=`hg identify -n`
export REVID=`hg identify -i`

echo "revno,revid,language,area,count" > stats/loc.csv
awk '{if (NF==7 && $1 !~ /\-/) printf("%s,%s,%s,%s,%s\n", ENVIRON["REVNO"], ENVIRON["REVID"], $1, FILENAME, $3) >> "stats/loc.csv" }' stats/*.count

nosetests --with-coverage --cover-package=dexy,handlers,reporters &> stats/nose.cover

# Fetch first line - calc number of tests passed/failed
awk 'BEGIN {FS="."} { if (NR==1) print NF-1, "passing tests"}' stats/nose.cover
awk 'BEGIN {FS="E"} { if (NR==1) print NF-1, "tests with errors"}' stats/nose.cover

echo "revno,revid,coverage" > stats/coverage.csv
awk '{ if ($1 == "TOTAL") printf("%s,%s,%s\n", ENVIRON["REVNO"], ENVIRON["REVID"], 1-$3/$2) >> "stats/coverage.csv"}' stats/nose.cover 

# current uncommitted code
export UNCOMMITTED_LINES=`hg diff | wc -l | awk '{print $1}'`
echo "currently there are $UNCOMMITTED_LINES lines of changed code"


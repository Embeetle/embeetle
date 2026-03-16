#/bin/sh
echo "Starting fix_warnings test at `pwd` ..."
source=$(dirname $0)
if [ "$(realpath $source)" == "$(pwd -P)" ]; then
    echo "$0: please run me from another directory"
    exit 1
fi
data=test_data
rm -rf $data
cp -a $source/$data .
python3.7 $source/fix_warnings.py $data

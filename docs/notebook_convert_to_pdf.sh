#! /bin/sh

ipython nbconvert \
    --to latex \
    --post PDF \
    --config notebook_config.py \
    --template notebook_template.tplx \
    introduction_to_coma.ipynb

name="introduction_to_coma"
for suffix in ".aux" ".idx" ".log" ".out" ".tex" ".toc" "_files"; do
    if [ -f ${name}${suffix} ]; then
        rm ${name}${suffix}
    fi
    if [ -d ${name}${suffix} ]; then
        rm -r ${name}${suffix}
    fi
done

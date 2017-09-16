#!/bin/bash

paths=`find /mnt/ -maxdepth 1 -name sd* -type d`
srcPath="./src-files"

for p in $paths ; do
	echo "Copying files to ${p}"
	srcFiles=("$srcPath/"*)
	nSF=${#srcFiles[@]}
	cn=0
	while [[ $cn -lt $nSF ]]; do
		sf=${srcFiles[${cn}]}
		fName=`basename "${sf}"`
		echo -n "`expr ${cn} + 1`/${nSF}    ${fName} ..."
		src_size=`ls -l "${sf}" | cut -d' ' -f5`
		cp "${sf}" "${p}/" &
		curr_size="0"
		while [ "${src_size}" != "${curr_size}" ] ; do
			sleep 1
			curr_size=`ls -l "${p}/${fName}" | cut -d' ' -f5`
			echo -n "."
		done
		echo " OK"
		cn=`expr $cn + 1`
	done
done

#!/bin/bash

paths=`find /mnt/ -maxdepth 1 -name sd* -type d`
for p in ${paths}; do
	umount ${p}
	rmdir ${p}
done

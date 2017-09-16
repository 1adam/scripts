#!/bin/bash

parts=`find /dev/sd?? \! -name sda*`

for p in ${parts}
do
	pname=`basename ${p}`
	mkdir "/mnt/${pname}"
	mount -t auto "${p}" "/mnt/${pname}"
done

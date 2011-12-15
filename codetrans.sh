#!/bin/bash
echo 'If you want someone get code from your machine, run this and stay'
echo 'start code transfer service...'
echo 'now others can get your code by:'
ip0=`ifconfig en0|egrep -o '([0-9]{1,3}\.){3}[0-9]{1,3}'|sed -n '1p'`
ip1=`ifconfig en1|egrep -o '([0-9]{1,3}\.){3}[0-9]{1,3}'|sed -n '1p'`

if [ -n "$ip0" ];then
    echo '    git pull --rebase git://'$ip0'/'
fi

if [ -n "$ip1" ];then
    echo 'or  git pull --rebase git://'$ip1'/'
fi

if [ "$ip0" = "" -a "$ip1" = "" ];then
    echo 'connect to network first and rerun this code.'
fi
have_say=`which say`
if [ -n "$have_say" ];then
	say "Pair, get the code!"
fi
echo 'ctrl+c to stop.'
git daemon --base-path=. --export-all

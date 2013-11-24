test "1" = "$(egrep -o '^(BUG|FEATURE|OTHER):' "$1" | sort | uniq -c |
    sed -e 's/[ ]*//g' -e 's/BUG://g' -e 's/FEATURE://g' -e 's/OTHER://g' )" || {
	echo >&2 "Must start commit message with BUG: or FEATURE: or OTHER:"
	exit 1
}

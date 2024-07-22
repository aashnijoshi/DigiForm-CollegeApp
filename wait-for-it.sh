#!/usr/bin/env bash
#   Use this script to test if a given TCP host/port are available

set -e

TIMEOUT=15
QUIET=0

echoerr() {
    if [[ $QUIET -ne 1 ]]; then echo "$@" 1>&2; fi
}

usage() {
    echo "Usage: $0 host:port [-s] [-t timeout] [-- command args]"
    echo "  -s | --strict               Only execute subcommand if the test succeeds"
    echo "  -q | --quiet                Don't output any status messages"
    echo "  -t TIMEOUT | --timeout=timeout  Timeout in seconds, zero for no timeout"
    exit 1
}

wait_for() {
    if [[ $TIMEOUT -gt 0 ]]; then
        echoerr "$0: waiting $TIMEOUT seconds for $HOST:$PORT"
    else
        echoerr "$0: waiting for $HOST:$PORT without a timeout"
    fi
    start_ts=$(date +%s)
    while :
    do
        if [[ $ISBUSY -eq 1 ]]; then
            nc -z $HOST $PORT
            result=$?
        else
            (echo > /dev/tcp/$HOST/$PORT) >/dev/null 2>&1
            result=$?
        fi
        if [[ $result -eq 0 ]]; then
            end_ts=$(date +%s)
            echoerr "$0: $HOST:$PORT is available after $((end_ts - start_ts)) seconds"
            break
        fi
        sleep 1
    done
    return $result
}

while [[ $# -gt 0 ]]
do
    case "$1" in
        *:* )
        HOST=$(printf "%s\n" "$1"| cut -d : -f 1)
        PORT=$(printf "%s\n" "$1"| cut -d : -f 2)
        shift 1
        ;;
        -q | --quiet)
        QUIET=1
        shift
        ;;
        -s | --strict)
        STRICT=1
        shift
        ;;
        -t)
        TIMEOUT="$2"
        if [[ $TIMEOUT == "" ]]; then break; fi
        shift 2
        ;;
        --timeout=*)
        TIMEOUT="${1#*=}"
        shift 1
        ;;
        --)
        shift
        break
        ;;
        --help)
        usage
        ;;
        *)
        echoerr "Unknown argument: $1"
        usage
        ;;
    esac
done

if [[ "$HOST" == "" || "$PORT" == "" ]]; then
    echoerr "Error: you need to provide a host and port to test."
    usage
fi

wait_for

shift $((OPTIND-1))

if [[ $# -gt 0 ]]; then
    if [[ $result -ne 0 && $STRICT -eq 1 ]]; then
        echoerr "$0: strict mode, refusing to execute subprocess"
        exit $result
    fi
    exec "$@"
else
    exit $result
fi
